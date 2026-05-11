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
    def __init__(self, message=''):
        self.message = message


class SecretServerClientError(SecretServerError):
    pass


class SecretServerServiceError(SecretServerError):
    pass


class MockSecretServer(MagicMock):
    RESPONSE = '{"foo": "bar"}'

    def get_secret_json(self, path, query_params=None):
        return self.RESPONSE


class MockFaultySecretServer(MagicMock):
    def get_secret_json(self, path, query_params=None):
        raise SecretServerError


class MockSecretServerStaleFirstCall(MagicMock):
    """Class-level counter: the first get_secret_json across all instances
    raises a client error (simulating a stale cached token); subsequent calls
    succeed. The plugin's retry path must build a second TSSClient, which gets
    a fresh instance of this class, and the counter persists across them.

    Note: type(self) on a MagicMock subclass returns a per-instance dynamic
    subclass, not the user-defined parent class. We reference the parent
    class by name explicitly so the counter actually persists across
    instances."""
    RESPONSE = '{"foo": "bar"}'
    _counter = 0

    @classmethod
    def reset(cls):
        cls._counter = 0

    def get_secret_json(self, path, query_params=None):
        MockSecretServerStaleFirstCall._counter += 1
        if MockSecretServerStaleFirstCall._counter == 1:
            raise SecretServerClientError('401 Unauthorized')
        return self.RESPONSE


class MockSecretServerServiceError(MagicMock):
    def get_secret_json(self, path, query_params=None):
        raise SecretServerServiceError('500 Internal Server Error')


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
        tss._reset_cache()
        self.lookup = lookup_loader.get("delinea.platform_secretserver.tss")

    def tearDown(self):
        tss._reset_cache()

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

        tss._reset_cache()

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
                SecretServerError=SecretServerError,
                AccessTokenAuthorizer=MagicMock,
                PasswordGrantAuthorizer=MagicMock,
                DomainPasswordGrantAuthorizer=MagicMock)
class TestModuleCache(TestCase):
    def setUp(self):
        tss._reset_cache()
        self.lookup = lookup_loader.get("delinea.platform_secretserver.tss")

    def tearDown(self):
        tss._reset_cache()

    def _run(self, **kwargs):
        base_kwargs = {"base_url": "url", "username": "u", "password": "p"}
        base_kwargs.update(kwargs)
        with patch(make_absolute('SecretServer'), MockSecretServer):
            return self.lookup.run([1], [], **base_kwargs)

    def test_module_cache_reuses_client_for_same_credentials(self):
        self._run(base_url='u', username='alice', password='p')
        self.assertEqual(len(tss._client_cache), 1)
        cached_client = next(iter(tss._client_cache.values()))

        self._run(base_url='u', username='alice', password='p')
        self.assertEqual(len(tss._client_cache), 1)
        self.assertIs(next(iter(tss._client_cache.values())), cached_client)

    def test_module_cache_separates_clients_by_credential_identity(self):
        self._run(base_url='u', username='alice', password='p')
        self._run(base_url='u', username='bob', password='p')
        self.assertEqual(len(tss._client_cache), 2)

    def test_module_cache_bypassed_when_token_supplied(self):
        self._run(base_url='u', token='tok')
        self._run(base_url='u', token='tok')
        self.assertEqual(len(tss._client_cache), 0)

    def test_reset_cache_clears_state(self):
        self._run(base_url='u', username='alice', password='p')
        self.assertEqual(len(tss._client_cache), 1)
        tss._reset_cache()
        self.assertEqual(tss._client_cache, {})


@patch.multiple(TSS_IMPORT_PATH,
                HAS_TSS_SDK=True,
                SecretServerError=SecretServerError,
                SecretServerClientError=SecretServerClientError,
                HAS_SS_CLIENT_ERROR=True)
class TestCacheInvalidationOnAuthError(TestCase):
    def setUp(self):
        tss._reset_cache()
        MockSecretServerStaleFirstCall.reset()
        self.lookup = lookup_loader.get("delinea.platform_secretserver.tss")

    def tearDown(self):
        tss._reset_cache()
        MockSecretServerStaleFirstCall.reset()

    def test_client_error_invalidates_cache_and_retry_succeeds(self):
        with patch(make_absolute('SecretServer'), MockSecretServerStaleFirstCall):
            result = self.lookup.run(
                [1], [], base_url='u', username='alice', password='p'
            )
            self.assertEqual(result, [MockSecretServerStaleFirstCall.RESPONSE])
            self.assertEqual(MockSecretServerStaleFirstCall._counter, 2)
            self.assertEqual(len(tss._client_cache), 1)

    def test_service_error_propagates_without_retry(self):
        with patch(make_absolute('SecretServer'), MockSecretServerServiceError):
            with self.assertRaises(tss.AnsibleError):
                self.lookup.run(
                    [1], [], base_url='u', username='alice', password='p'
                )
            self.assertEqual(len(tss._client_cache), 1)

    def test_persistent_client_error_propagates_after_one_retry(self):
        class _AlwaysClientError(MagicMock):
            def get_secret_json(self, path, query_params=None):
                raise SecretServerClientError('401 Unauthorized')

        with patch(make_absolute('SecretServer'), _AlwaysClientError):
            with self.assertRaises(tss.AnsibleError):
                self.lookup.run(
                    [1], [], base_url='u', username='alice', password='p'
                )


@patch.multiple(TSS_IMPORT_PATH,
                HAS_TSS_SDK=True,
                SecretServerError=SecretServerError,
                HAS_SS_CLIENT_ERROR=False)
class TestCacheNoRetryWhenSDKLacksClientError(TestCase):
    def setUp(self):
        tss._reset_cache()
        MockSecretServerStaleFirstCall.reset()
        self.lookup = lookup_loader.get("delinea.platform_secretserver.tss")

    def tearDown(self):
        tss._reset_cache()
        MockSecretServerStaleFirstCall.reset()

    def test_no_retry_path_when_sdk_lacks_client_error_class(self):
        with patch(make_absolute('SecretServer'), MockSecretServerStaleFirstCall):
            with self.assertRaises(tss.AnsibleError):
                self.lookup.run(
                    [1], [], base_url='u', username='alice', password='p'
                )
            self.assertEqual(MockSecretServerStaleFirstCall._counter, 1)
