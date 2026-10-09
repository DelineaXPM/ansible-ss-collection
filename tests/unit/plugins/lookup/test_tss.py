# -*- coding: utf-8 -*-
# (c) 2023, Delinea <https://delinea.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import shutil
import stat
import tempfile

from ansible_collections.delinea.platform_secretserver.tests.unit.compat.unittest import TestCase
from ansible_collections.delinea.platform_secretserver.tests.unit.compat.mock import (
    patch,
    DEFAULT,
    MagicMock,
)
from ansible_collections.delinea.platform_secretserver.plugins.lookup import tss
from ansible.plugins.loader import lookup_loader


TSS_IMPORT_PATH = 'ansible_collections.delinea.platform_secretserver.plugins.lookup.tss'


def make_absolute(name):
    return '.'.join([TSS_IMPORT_PATH, name])


class SecretServerError(Exception):
    def __init__(self):
        self.message = ''


class MockSecretServer(MagicMock):
    RESPONSE = '{"foo": "bar"}'

    def get_secret_json(self, path, query_params=None):
        return self.RESPONSE


class MockFaultySecretServer(MagicMock):
    def get_secret_json(self, path, query_params=None):
        raise SecretServerError


class MockAttachmentResponse(object):
    """Stands in for the C(requests) response the SDK stores in an item."""

    def __init__(self, content=None, error=None):
        self._content = content
        self._error = error

    @property
    def content(self):
        if self._error is not None:
            raise self._error
        return self._content


class MockAttachmentSecretServer(MagicMock):
    """A server whose secret carries one file attachment."""

    CONTENT = b'-----BEGIN PRIVATE KEY-----'
    ITEM_VALUE = None
    FILE_ATTACHMENT_ID = 42

    def get_secret(self, secret_id, fetch_file_attachments=True, query_params=None):
        return {
            'id': secret_id,
            'items': [
                {
                    'slug': 'private-key',
                    'isFile': True,
                    'fileAttachmentId': self.FILE_ATTACHMENT_ID,
                    'itemValue': self.ITEM_VALUE,
                },
                {
                    'slug': 'username',
                    'isFile': False,
                    'fileAttachmentId': None,
                    'itemValue': 'user.name',
                },
            ],
        }


@patch(make_absolute('SecretServer'), MockSecretServer())
class TestTSSClient(TestCase):
    def setUp(self):
        self.server_params = {
            'base_url': '',
            'username': '',
            'domain': '',
            'password': '',
            'api_path_uri': '',
            'token_path_uri': '',
        }

    def test_from_params(self):
        with patch(make_absolute('HAS_TSS_AUTHORIZER'), False):
            self.assert_client_version('v0')

            with patch.dict(self.server_params, {'domain': 'foo'}):
                with self.assertRaises(tss.AnsibleError):
                    self._get_client()

        with patch.multiple(TSS_IMPORT_PATH,
                            HAS_TSS_AUTHORIZER=True,
                            PasswordGrantAuthorizer=DEFAULT,
                            DomainPasswordGrantAuthorizer=DEFAULT):

            self.assert_client_version('v1')

            with patch.dict(self.server_params, {'domain': 'foo'}):
                self.assert_client_version('v1')

    def assert_client_version(self, version):
        version_to_class = {
            'v0': tss.TSSClientV0,
            'v1': tss.TSSClientV1
        }

        client = self._get_client()
        self.assertIsInstance(client, version_to_class[version])

    def _get_client(self):
        return tss.TSSClient.from_params(**self.server_params)


class TestLookupModule(TestCase):
    VALID_TERMS = [1]
    INVALID_TERMS = ['foo']

    def setUp(self):
        self.lookup = lookup_loader.get("delinea.platform_secretserver.tss")

    @patch.multiple(TSS_IMPORT_PATH,
                    HAS_TSS_SDK=False,
                    SecretServer=MockSecretServer)
    def test_missing_sdk(self):
        with self.assertRaises(tss.AnsibleError):
            self._run_lookup(self.VALID_TERMS)

    @patch.multiple(TSS_IMPORT_PATH,
                    HAS_TSS_SDK=True,
                    SecretServerError=SecretServerError)
    def test_get_secret_json(self):
        with patch(make_absolute('SecretServer'), MockSecretServer):
            self.assertListEqual([MockSecretServer.RESPONSE], self._run_lookup(self.VALID_TERMS))

            with self.assertRaises(tss.AnsibleOptionsError):
                self._run_lookup(self.INVALID_TERMS)

        with patch(make_absolute('SecretServer'), MockFaultySecretServer):
            with self.assertRaises(tss.AnsibleError):
                self._run_lookup(self.VALID_TERMS)

    @patch.multiple(TSS_IMPORT_PATH,
                    HAS_TSS_SDK=True,
                    SecretServerError=SecretServerError)
    def test_get_secret_with_comment(self):
        with patch(make_absolute('SecretServer'), MockSecretServer):
            result = self._run_lookup(self.VALID_TERMS, comment='Test audit comment')
            self.assertListEqual([MockSecretServer.RESPONSE], result)

            result = self._run_lookup(self.VALID_TERMS)
            self.assertListEqual([MockSecretServer.RESPONSE], result)

    def _run_lookup(self, terms, variables=None, **kwargs):
        variables = variables or []
        default_kwargs = {"base_url": "dummy", "username": "dummy", "password": "dummy"}
        default_kwargs.update(kwargs)

        return self.lookup.run(terms, variables, **default_kwargs)


@patch.multiple(TSS_IMPORT_PATH,
                HAS_TSS_SDK=True,
                HAS_TSS_AUTHORIZER=False,
                SecretServerError=SecretServerError)
class TestFileAttachmentDownload(TestCase):
    """Covers the download path that used to destroy files on failure."""

    SECRET_ID = 102
    STALE_CONTENT = b'content written by an earlier run'

    def setUp(self):
        self.lookup = lookup_loader.get("delinea.platform_secretserver.tss")
        self.download_path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.download_path, True)
        self.destination = os.path.join(
            self.download_path, '{0}_private-key'.format(self.SECRET_ID)
        )

    def test_attachment_is_written(self):
        secret = self._run_lookup(MockAttachmentResponse(
            content=MockAttachmentSecretServer.CONTENT))[0]

        self.assertEqual(
            MockAttachmentSecretServer.CONTENT, self._read_destination()
        )
        self.assertEqual(
            '*** Not Valid For Display ***', secret['items'][0]['itemValue']
        )
        self.assertEqual('user.name', secret['items'][1]['itemValue'])
        self.assertEqual([], self._staging_files())

    def test_failed_download_keeps_existing_file(self):
        self._write_destination(self.STALE_CONTENT)

        with self.assertRaises(tss.AnsibleError) as raised:
            self._run_lookup(MockAttachmentResponse(
                error=IOError('connection aborted')))

        self.assertIn('private-key', str(raised.exception))
        self.assertIn('connection aborted', str(raised.exception))
        self.assertEqual(self.STALE_CONTENT, self._read_destination())
        self.assertEqual([], self._staging_files())

    def test_failed_download_creates_no_file(self):
        with self.assertRaises(tss.AnsibleError):
            self._run_lookup(MockAttachmentResponse(
                error=IOError('connection aborted')))

        self.assertFalse(os.path.exists(self.destination))
        self.assertEqual([], self._staging_files())

    def test_failed_write_keeps_existing_file(self):
        self._write_destination(self.STALE_CONTENT)

        # A payload that is not bytes fails once the write is under way, which
        # is where the destination used to have been truncated already.
        with self.assertRaises(tss.AnsibleError) as raised:
            self._run_lookup(MockAttachmentResponse(content='not bytes'))

        self.assertIn('Failed to write', str(raised.exception))
        self.assertEqual(self.STALE_CONTENT, self._read_destination())
        self.assertEqual([], self._staging_files())

    def test_missing_content_propagates(self):
        with self.assertRaises(tss.AnsibleError) as raised:
            self._run_lookup('not a response')

        self.assertIn('no file content', str(raised.exception))
        self.assertFalse(os.path.exists(self.destination))

    def test_file_field_without_attachment_is_not_fatal(self):
        self._write_destination(self.STALE_CONTENT)

        secret = self._run_lookup(
            'not a response', file_attachment_id=None)[0]

        self.assertEqual(self.STALE_CONTENT, self._read_destination())
        self.assertEqual(
            '*** Not Valid For Display ***', secret['items'][0]['itemValue']
        )

    def test_invalid_download_path(self):
        with self.assertRaises(tss.AnsibleOptionsError):
            self._run_lookup(
                MockAttachmentResponse(
                    content=MockAttachmentSecretServer.CONTENT),
                file_download_path=os.path.join(self.download_path, 'absent'),
            )

    def test_replacement_does_not_inherit_the_old_mode(self):
        self._require_posix()
        self._set_umask(0o022)
        self._write_destination(self.STALE_CONTENT)
        os.chmod(self.destination, 0o600)

        self._run_lookup(MockAttachmentResponse(
            content=MockAttachmentSecretServer.CONTENT))

        self.assertEqual(0o644, self._mode_of_destination())

    def test_new_file_uses_the_umask_mode(self):
        self._require_posix()
        self._set_umask(0o022)
        self.assertFalse(os.path.exists(self.destination))

        self._run_lookup(MockAttachmentResponse(
            content=MockAttachmentSecretServer.CONTENT))

        self.assertEqual(0o644, self._mode_of_destination())

    def test_a_tighter_umask_is_honoured(self):
        self._require_posix()
        self._set_umask(0o077)

        self._run_lookup(MockAttachmentResponse(
            content=MockAttachmentSecretServer.CONTENT))

        self.assertEqual(0o600, self._mode_of_destination())

    def _require_posix(self):
        if os.name != 'posix':
            self.skipTest('file modes are not meaningful on this platform')

    def _set_umask(self, umask):
        self.addCleanup(os.umask, os.umask(umask))

    def _mode_of_destination(self):
        return stat.S_IMODE(os.stat(self.destination).st_mode)

    def test_staging_cleanup_failure_is_only_a_warning(self):
        with patch(make_absolute('display')) as display:
            tss.TSSClient._remove_quietly(
                os.path.join(self.download_path, '.tss-never-created.part'))

        display.warning.assert_called_once()
        self.assertIn('.tss-never-created.part', display.warning.call_args[0][0])

    def _run_lookup(self, item_value, file_attachment_id=42, **kwargs):
        server = MockAttachmentSecretServer
        with patch.multiple(server,
                            ITEM_VALUE=item_value,
                            FILE_ATTACHMENT_ID=file_attachment_id):
            with patch(make_absolute('SecretServer'), server):
                lookup_kwargs = {
                    'base_url': 'dummy',
                    'username': 'dummy',
                    'password': 'dummy',
                    'fetch_attachments': True,
                    'file_download_path': self.download_path,
                }
                lookup_kwargs.update(kwargs)

                return self.lookup.run([self.SECRET_ID], [], **lookup_kwargs)

    def _write_destination(self, content):
        with open(self.destination, 'wb') as handle:
            handle.write(content)

    def _read_destination(self):
        with open(self.destination, 'rb') as handle:
            return handle.read()

    def _staging_files(self):
        return [
            name for name in os.listdir(self.download_path)
            if name.startswith('.tss-')
        ]


class TestSdkErrorFormatting(TestCase):
    def test_message_from_a_service_response(self):
        response = MagicMock(status_code=500, text='  Internal Server Error  ')
        error = SecretServerError()
        error.message = response

        self.assertEqual(
            'HTTP 500: Internal Server Error',
            tss.LookupModule._format_sdk_error(error),
        )

    def test_message_from_a_bodyless_service_response(self):
        response = MagicMock(status_code=502, text='')
        error = SecretServerError()
        error.message = response

        self.assertEqual(
            'HTTP 502', tss.LookupModule._format_sdk_error(error)
        )

    def test_message_from_a_client_error(self):
        error = SecretServerError()
        error.message = 'Access Denied'

        self.assertEqual(
            'Access Denied', tss.LookupModule._format_sdk_error(error)
        )

    def test_message_falls_back_to_the_exception(self):
        error = SecretServerError()
        error.message = None

        self.assertEqual(
            'SecretServerError', tss.LookupModule._format_sdk_error(error)
        )
