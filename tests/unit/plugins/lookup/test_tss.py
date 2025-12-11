# -*- coding: utf-8 -*-
# (c) 2023, Delinea <https://delinea.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

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
