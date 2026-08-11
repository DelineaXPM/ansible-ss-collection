# -*- coding: utf-8 -*-
# (c) 2023, Delinea <https://delinea.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest

from ansible_collections.delinea.platform_secretserver.tests.unit.compat.unittest import TestCase
from ansible_collections.delinea.platform_secretserver.tests.unit.compat.mock import (
    patch,
    DEFAULT,
    MagicMock,
)
from ansible_collections.delinea.platform_secretserver.plugins.lookup import tss
from ansible.plugins.loader import lookup_loader

try:
    from delinea.secrets.server import (
        SecretServer as RealSecretServer,
        SecretServerClientError as RealSecretServerClientError,
    )
    HAS_REAL_SDK = True
except ImportError:
    HAS_REAL_SDK = False


TSS_IMPORT_PATH = 'ansible_collections.delinea.platform_secretserver.plugins.lookup.tss'


def make_absolute(name):
    return '.'.join([TSS_IMPORT_PATH, name])


class SecretServerError(Exception):
    # FAITHFUL to python-tss-sdk <= 2.0.1: __init__ accepts ``response`` but
    # DISCARDS it -- only .message is stored (verified against the installed
    # SDK). Tests that simulate a fixed SDK (the upstream ADO 734475 change
    # adds ``self.response = response``) attach the attribute explicitly via
    # make_client_error(status=...). Keeping the double honest here is what
    # lets the suite distinguish "works today" from "works once the SDK is
    # fixed".
    def __init__(self, message='', response=None):
        self.message = message


class SecretServerClientError(SecretServerError):
    pass


class SecretServerServiceError(SecretServerError):
    pass


def make_response(status_code, headers=None):
    """A minimal stand-in for a requests.Response."""
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers if headers is not None else {}
    return response


def make_client_error(message, status=None, headers=None):
    """Build a SecretServerClientError. With ``status`` set, simulates a
    FIXED SDK that exposes ``error.response``; without it, simulates today's
    SDK (<= 2.0.1), which discards the response."""
    error = SecretServerClientError(message)
    if status is not None:
        error.response = make_response(status, headers)
    return error


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
            # No response attached -- exactly what today's SDK raises.
            raise SecretServerClientError('401 Unauthorized')
        return self.RESPONSE


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

    def test_module_cache_caches_token_clients_too(self):
        # ADO 734475 Phase 2: token-auth clients are cached as well (under a
        # hashed key), so AccessTokenAuthorizer -- whose __init__ probes the
        # health endpoints eagerly -- is built once per process, not per
        # lookup().
        self._run(base_url='u', token='tok')
        self.assertEqual(len(tss._client_cache), 1)
        cached_client = next(iter(tss._client_cache.values()))
        self._run(base_url='u', token='tok')
        self.assertEqual(len(tss._client_cache), 1)
        self.assertIs(next(iter(tss._client_cache.values())), cached_client)

    def test_reset_cache_clears_state(self):
        self._run(base_url='u', username='alice', password='p')
        self.assertEqual(len(tss._client_cache), 1)
        tss._reset_cache()
        self.assertEqual(len(tss._client_cache), 0)


TOKEN = 'super-secret-raw-token-value'


@patch.multiple(TSS_IMPORT_PATH,
                HAS_TSS_SDK=True,
                SecretServerError=SecretServerError,
                AccessTokenAuthorizer=MagicMock,
                PasswordGrantAuthorizer=MagicMock,
                DomainPasswordGrantAuthorizer=MagicMock)
class TestTokenClientCache(TestCase):
    """ADO 734475 Phase 2: the token-auth path is the zero-config lever --
    AccessTokenAuthorizer probes the health endpoints eagerly in __init__,
    so without caching every token-auth lookup() re-probes. The cache key is
    a salted SHA-256 digest of the token, never the token itself."""

    def setUp(self):
        tss._reset_cache()
        self.lookup = lookup_loader.get("delinea.platform_secretserver.tss")

    def tearDown(self):
        tss._reset_cache()

    def _run(self, **kwargs):
        base_kwargs = {"base_url": "https://tenant.example.com", "token": TOKEN}
        base_kwargs.update(kwargs)
        with patch(make_absolute('SecretServer'), MockSecretServer):
            return self.lookup.run([1], [], **base_kwargs)

    def _flatten_keys(self):
        parts = []
        for key in tss._client_cache:
            for element in key:
                parts.append(str(element))
        return parts

    def test_token_lookups_reuse_one_client(self):
        self._run()
        self.assertEqual(len(tss._client_cache), 1)
        cached_client = next(iter(tss._client_cache.values()))
        for _iteration in range(19):
            self._run()
        self.assertEqual(len(tss._client_cache), 1)
        self.assertIs(next(iter(tss._client_cache.values())), cached_client)

    def test_cache_key_is_salted_digest_not_token(self):
        self._run()
        parts = self._flatten_keys()
        # the raw token must not appear in any key element...
        for part in parts:
            self.assertNotIn(TOKEN, part)
        # ...and the token element must be a sha256 hexdigest (64 hex chars)
        digests = [p for p in parts if len(p) == 64 and all(c in '0123456789abcdef' for c in p)]
        self.assertEqual(len(digests), 1)

    def test_key_salt_is_per_process_random(self):
        # sha256(token) alone would be precomputable offline; the salt must
        # participate in the digest.
        import hashlib
        self._run()
        unsalted = hashlib.sha256(TOKEN.encode('utf-8')).hexdigest()
        self.assertNotIn(unsalted, self._flatten_keys())

    def test_raw_token_absent_from_verbose_logs(self):
        with patch.object(tss.display, 'vvv') as mock_vvv, \
                patch.object(tss.display, 'debug') as mock_debug, \
                patch.object(tss.display, 'v', create=True) as mock_v:
            self._run()
            self._run()
        for mock in (mock_vvv, mock_debug, mock_v):
            for call in mock.call_args_list:
                for arg in call.args:
                    self.assertNotIn(TOKEN, str(arg))

    def test_distinct_tokens_get_distinct_entries(self):
        self._run(token='token-aaa')
        self._run(token='token-bbb')
        self.assertEqual(len(tss._client_cache), 2)
        clients = list(tss._client_cache.values())
        self.assertIsNot(clients[0], clients[1])

    def test_token_and_password_keys_never_collide(self):
        self._run()
        self._run(token=None, username='alice', password='p')
        self.assertEqual(len(tss._client_cache), 2)

    def test_cache_is_bounded_with_lru_eviction(self):
        with patch.object(tss, '_CLIENT_CACHE_MAXSIZE', 4):
            for i in range(6):
                self._run(token='token-%d' % i)
            self.assertEqual(len(tss._client_cache), 4)
            # oldest entries evicted: token-0 and token-1 rebuild on next use
            survivors = list(tss._client_cache.keys())
            self._run(token='token-5')  # hit: must not grow the cache
            self.assertEqual(len(tss._client_cache), 4)
            self.assertEqual(set(tss._client_cache.keys()), set(survivors))

    def test_lru_hit_refreshes_recency(self):
        with patch.object(tss, '_CLIENT_CACHE_MAXSIZE', 2):
            self._run(token='token-a')
            client_a = next(iter(tss._client_cache.values()))
            self._run(token='token-b')
            self._run(token='token-a')   # refresh a: b is now oldest
            self._run(token='token-c')   # evicts b, not a
            self.assertEqual(len(tss._client_cache), 2)
            # token-a survived the eviction because the hit refreshed it
            self.assertIn(client_a, list(tss._client_cache.values()))

    def test_threaded_lookups_converge_on_one_client(self):
        import threading as _threading
        results = []
        errors = []

        def worker():
            try:
                with patch(make_absolute('SecretServer'), MockSecretServer):
                    self.lookup.run(
                        [1], [],
                        base_url='https://tenant.example.com', token=TOKEN)
                with tss._client_cache_lock:
                    results.append(next(iter(tss._client_cache.values())))
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [_threading.Thread(target=worker) for _index in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        self.assertEqual(len(tss._client_cache), 1)
        # every thread observed the same converged client
        self.assertEqual(len(set(id(client) for client in results)), 1)


@patch.multiple(TSS_IMPORT_PATH,
                HAS_TSS_SDK=True,
                SecretServerError=SecretServerError,
                SecretServerClientError=SecretServerClientError,
                HAS_SS_CLIENT_ERROR=True)
class TestCacheInvalidationOnAuthError(TestCase):
    """Stale-cached-token recovery: a client that WAS working (cache hit)
    starts failing with a client error -> drop it, rebuild, retry once.
    All scenarios prime the cache first, because a fresh build never
    retries (see TestWafSafeRetryPolicy's cache-hit gate)."""

    def setUp(self):
        tss._reset_cache()
        MockSecretServerScripted.reset()
        self.lookup = lookup_loader.get("delinea.platform_secretserver.tss")

    def tearDown(self):
        tss._reset_cache()
        MockSecretServerScripted.reset()

    def _run(self):
        with patch(make_absolute('SecretServer'), MockSecretServerScripted):
            return self.lookup.run(
                [1], [], base_url='u', username='alice', password='p'
            )

    def test_client_error_invalidates_cache_and_retry_succeeds(self):
        MockSecretServerScripted.reset(
            ['ok', SecretServerClientError('401 Unauthorized'), 'ok'])
        self._run()  # prime
        result = self._run()
        self.assertEqual(result, [MockSecretServerScripted.RESPONSE])
        self.assertEqual(MockSecretServerScripted._calls, 3)
        self.assertEqual(len(tss._client_cache), 1)

    def test_service_error_propagates_without_retry(self):
        MockSecretServerScripted.reset(
            ['ok', SecretServerServiceError('500 Internal Server Error')])
        self._run()  # prime
        with self.assertRaises(tss.AnsibleError):
            self._run()
        self.assertEqual(MockSecretServerScripted._calls, 2)
        self.assertEqual(len(tss._client_cache), 1)

    def test_persistent_client_error_propagates_after_one_retry(self):
        MockSecretServerScripted.reset(
            ['ok',
             SecretServerClientError('401 Unauthorized'),
             SecretServerClientError('401 Unauthorized')])
        self._run()  # prime
        with self.assertRaises(tss.AnsibleError):
            self._run()
        # prime + failing attempt + exactly one retry
        self.assertEqual(MockSecretServerScripted._calls, 3)


class MockSecretServerScripted(MagicMock):
    """Plays a per-call script: element i of ``SCRIPT`` decides call i+1 --
    the string 'ok' returns RESPONSE, an exception instance is raised. Calls
    beyond the script repeat the last element. Class-level state for the
    same reason as MockSecretServerStaleFirstCall: a retry builds a fresh
    instance, and the counter must persist across instances.

    The retry gate means only a CACHED client's error may retry, so tests
    that exercise the retry path must prime the cache with a successful
    call first -- hence scripts like ['ok', error, 'ok']."""
    RESPONSE = '{"foo": "bar"}'
    SCRIPT = []
    _calls = 0

    @classmethod
    def reset(cls, script=None):
        cls._calls = 0
        cls.SCRIPT = list(script) if script else []

    def get_secret_json(self, path, query_params=None):
        index = MockSecretServerScripted._calls
        MockSecretServerScripted._calls += 1
        script = MockSecretServerScripted.SCRIPT
        step = script[index] if index < len(script) else script[-1]
        if step == 'ok':
            return self.RESPONSE
        raise step


@patch.multiple(TSS_IMPORT_PATH,
                HAS_TSS_SDK=True,
                SecretServerError=SecretServerError,
                SecretServerClientError=SecretServerClientError,
                HAS_SS_CLIENT_ERROR=True,
                AccessTokenAuthorizer=MagicMock,
                PasswordGrantAuthorizer=MagicMock,
                DomainPasswordGrantAuthorizer=MagicMock)
class TestWafSafeRetryPolicy(TestCase):
    """ADO 734475: the drop-rebuild-retry path fires a fresh health-probe
    pair (plus an OAuth grant on the password path), so it must only run
    when a rebuild can actually help. Three gates compose:

    - CACHE-HIT GATE: only an error from a client REUSED from the cache may
      retry. A fresh build cannot hold a stale token, and in the
      fork-per-host burst that trips the WAF every worker is a cache miss,
      so nothing amplifies there.
    - TOKEN GATE: token auth NEVER retries -- re-presenting the same static
      token is guaranteed to fail identically.
    - STATUS GATE (only when python-tss-sdk exposes ``error.response``;
      <= 2.0.1 discards it): 401 and 400-invalid-token retry once; 403/429
      never, and the error names the WAF rate limit.

    Tests that exercise the retry path prime the cache with a successful
    call first: scripts like ['ok', error, 'ok'].
    """

    def setUp(self):
        tss._reset_cache()
        MockSecretServerScripted.reset()
        self.lookup = lookup_loader.get("delinea.platform_secretserver.tss")

    def tearDown(self):
        tss._reset_cache()
        MockSecretServerScripted.reset()

    def _run(self, **kwargs):
        run_kwargs = {'base_url': 'u', 'username': 'alice', 'password': 'p'}
        run_kwargs.update(kwargs)
        with patch(make_absolute('SecretServer'), MockSecretServerScripted):
            return self.lookup.run([1], [], **run_kwargs)

    def _run_expecting_error(self, **kwargs):
        with self.assertRaises(tss.AnsibleError) as ctx:
            self._run(**kwargs)
        return ctx.exception

    def _prime(self, **kwargs):
        # first lookup succeeds and populates the cache
        self._run(**kwargs)
        self.assertEqual(MockSecretServerScripted._calls, 1)

    # ------------------------- cache-hit gate -----------------------------

    def test_fresh_build_never_retries(self):
        # First-ever lookup fails -> the client was just built, a stale
        # token is impossible, and this is exactly the fork-per-host WAF
        # burst shape: no retry, no amplification.
        MockSecretServerScripted.reset([make_client_error('API_AccessDenied')])
        self._run_expecting_error()
        self.assertEqual(MockSecretServerScripted._calls, 1)

    def test_today_cached_password_client_retries_once_and_recovers(self):
        # The stale-cached-token case this retry exists for: a previously
        # good client starts failing; rebuild mints a fresh grant; retry
        # succeeds. Single-shot -> bounded 2x worst case.
        MockSecretServerScripted.reset(
            ['ok', make_client_error('API_AccessDenied'), 'ok'])
        self._prime()
        result = self._run()
        self.assertEqual(result, [MockSecretServerScripted.RESPONSE])
        self.assertEqual(MockSecretServerScripted._calls, 3)

    def test_today_cached_retry_failure_is_clean(self):
        MockSecretServerScripted.reset(
            ['ok',
             make_client_error('API_AccessDenied'),
             make_client_error('API_AccessDenied')])
        self._prime()
        self._run_expecting_error()
        self.assertEqual(MockSecretServerScripted._calls, 3)

    def test_today_token_client_error_never_retries(self):
        # Token gate beats the cache-hit gate: even a cached token client
        # never retries, and it stays cached (not dropped).
        token_kwargs = {'token': 'tok', 'username': None, 'password': None}
        MockSecretServerScripted.reset(
            ['ok', make_client_error('API_AccessDenied')])
        self._prime(**token_kwargs)
        cached_client = next(iter(tss._client_cache.values()))
        self._run_expecting_error(**token_kwargs)
        self.assertEqual(MockSecretServerScripted._calls, 2)
        self.assertEqual(len(tss._client_cache), 1)
        self.assertIs(next(iter(tss._client_cache.values())), cached_client)

    # ------------------------- status gate (fixed SDK) --------------------

    def test_403_does_not_rebuild_or_retry(self):
        MockSecretServerScripted.reset(
            ['ok', make_client_error('Forbidden', status=403)])
        self._prime()
        cached_client = next(iter(tss._client_cache.values()))
        self._run_expecting_error()
        # prime + one failing attempt: no retry
        self.assertEqual(MockSecretServerScripted._calls, 2)
        # client NOT dropped: same cached instance survives
        self.assertEqual(len(tss._client_cache), 1)
        self.assertIs(next(iter(tss._client_cache.values())), cached_client)

    def test_403_message_names_rate_limit(self):
        MockSecretServerScripted.reset(
            ['ok', make_client_error('Forbidden', status=403)])
        self._prime()
        error = self._run_expecting_error()
        self.assertIn('403', str(error))
        self.assertIn('rate limit', str(error).lower())

    def test_429_does_not_retry_and_surfaces_retry_after(self):
        MockSecretServerScripted.reset(
            ['ok', make_client_error('Too Many Requests', status=429,
                                     headers={'Retry-After': '60'})])
        self._prime()
        error = self._run_expecting_error()
        self.assertEqual(MockSecretServerScripted._calls, 2)
        self.assertEqual(len(tss._client_cache), 1)
        self.assertIn('Retry-After', str(error))
        self.assertIn('60', str(error))

    def test_401_on_cached_client_retries_once_and_recovers(self):
        MockSecretServerScripted.reset(
            ['ok', make_client_error('Unauthorized', status=401), 'ok'])
        self._prime()
        result = self._run()
        self.assertEqual(result, [MockSecretServerScripted.RESPONSE])
        self.assertEqual(MockSecretServerScripted._calls, 3)

    def test_401_on_token_path_still_never_retries(self):
        token_kwargs = {'token': 'tok', 'username': None, 'password': None}
        MockSecretServerScripted.reset(
            ['ok', make_client_error('Unauthorized', status=401)])
        self._prime(**token_kwargs)
        self._run_expecting_error(**token_kwargs)
        self.assertEqual(MockSecretServerScripted._calls, 2)

    def test_400_invalid_grant_retries_once(self):
        MockSecretServerScripted.reset(
            ['ok', make_client_error('invalid_grant: Grant has expired.', status=400), 'ok'])
        self._prime()
        result = self._run()
        self.assertEqual(result, [MockSecretServerScripted.RESPONSE])
        self.assertEqual(MockSecretServerScripted._calls, 3)

    def test_400_generic_does_not_retry(self):
        MockSecretServerScripted.reset(
            ['ok', make_client_error('Bad request', status=400)])
        self._prime()
        self._run_expecting_error()
        self.assertEqual(MockSecretServerScripted._calls, 2)

    def test_400_unrelated_expired_text_does_not_retry(self):
        # markers are anchored to OAuth error codes: server text like
        # "password expired" must not force a futile rebuild
        MockSecretServerScripted.reset(
            ['ok', make_client_error('The password expired for this user.', status=400)])
        self._prime()
        self._run_expecting_error()
        self.assertEqual(MockSecretServerScripted._calls, 2)

    # ------------------------- robustness -----------------------------

    def test_non_string_message_is_handled(self):
        # .message is server-controlled and not guaranteed to be a string:
        # a structured {"message": {...}} body arrives as a dict. Predicate
        # and formatting must not crash on it.
        MockSecretServerScripted.reset(
            ['ok', make_client_error({'nested': {'code': 1}}, status=400)])
        self._prime()
        self._run_expecting_error()
        self.assertEqual(MockSecretServerScripted._calls, 2)

    def test_missing_message_attribute_is_clean(self):
        # Defensive only: the real SDK always binds .message on errors it
        # successfully constructs (see the contract tests for what happens
        # when it cannot). Kept as a cheap guarantee for exotic SDK builds.
        error = make_client_error('x', status=400)
        del error.message
        MockSecretServerScripted.reset(['ok', error])
        self._prime()
        self._run_expecting_error()
        self.assertEqual(MockSecretServerScripted._calls, 2)

    def test_sdk_unbound_local_crash_surfaces_as_clean_error(self):
        # python-tss-sdk <= 2.0.1 process() raises UnboundLocalError (not
        # SecretServerError) when a 4xx JSON body lacks the keys it expects,
        # e.g. {"foo": 1} or {"error": {"code": 5}}. Must become a clean
        # AnsibleError, not a raw traceback.
        MockSecretServerScripted.reset(
            [UnboundLocalError("local variable 'message' referenced before assignment")])
        error = self._run_expecting_error()
        self.assertIn('malformed error response', str(error))
        self.assertIn('referenced before assignment', str(error))

    def test_sdk_type_error_crash_surfaces_as_clean_error(self):
        # ... and TypeError for non-dict JSON bodies (e.g. b"123").
        MockSecretServerScripted.reset(
            [TypeError("argument of type 'int' is not iterable")])
        error = self._run_expecting_error()
        self.assertIn('malformed error response', str(error))

    def test_bad_term_is_reported_as_options_error_not_server_error(self):
        # term=None (undefined variable) must surface as a caller-side
        # options error -- never misattributed to the server by the
        # malformed-response guard.
        MockSecretServerScripted.reset(['ok'])
        with patch(make_absolute('SecretServer'), MockSecretServerScripted):
            with self.assertRaises(tss.AnsibleOptionsError):
                self.lookup.run([None], [], base_url='u',
                                username='alice', password='p')
            with self.assertRaises(tss.AnsibleOptionsError):
                self.lookup.run([{'a': 1}], [], base_url='u',
                                username='alice', password='p')

    def test_client_build_failure_is_clean_and_never_retries(self):
        # AccessTokenAuthorizer.__init__ raises SecretServerError when both
        # health probes fail -- exactly what a WAF block produces. from_cache
        # must stay False (it is initialized BEFORE the try in run(); moving
        # it inside would raise UnboundLocalError here) and nothing may
        # retry: exactly one build attempt.
        with patch(make_absolute('TSSClient')) as mock_client:
            mock_client.from_params.side_effect = SecretServerError(
                'Unable to detect server type via health check endpoints.')
            error = self._run_expecting_error()
            self.assertEqual(mock_client.from_params.call_count, 1)
        self.assertIn('Unable to detect server type', str(error))

    def test_detection_failure_message_carries_waf_guidance(self):
        # The signature user-facing message for the ticket's condition (both
        # probes WAF-blocked at construction: no response, no status) must
        # name the WAF and suggest throttling -- it is the one message the
        # affected customer actually sees.
        with patch(make_absolute('TSSClient')) as mock_client:
            mock_client.from_params.side_effect = SecretServerError(
                'Unable to detect server type via health check endpoints.')
            error = self._run_expecting_error()
        text = str(error)
        self.assertIn('WAF rate limit', text)
        self.assertIn('serial:/forks:', text)

    def test_server_text_is_sanitized_and_truncated(self):
        hostile = '\x1b[31mALERT\x7f\x1b[0m ' + 'x' * 500
        MockSecretServerScripted.reset([make_client_error(hostile, status=403)])
        error = self._run_expecting_error()
        text = str(error)
        self.assertNotIn('\x1b', text)
        self.assertNotIn('\x7f', text)
        self.assertNotIn('x' * 300, text)


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


class RecordingSecretServer(MagicMock):
    """Captures the authorizer TSSClientV1 hands to SecretServer, so tests
    can inspect what the server-type override did to it."""
    RESPONSE = '{"foo": "bar"}'
    last_authorizer = None

    def __init__(self, *args, **kwargs):
        super(RecordingSecretServer, self).__init__()
        if len(args) >= 2:
            RecordingSecretServer.last_authorizer = args[1]

    def get_secret_json(self, path, query_params=None):
        return self.RESPONSE


class FakeLazyAuthorizer(object):
    """Mimics PasswordGrantAuthorizer/DomainPasswordGrantAuthorizer on
    python-tss-sdk <= 2.0.1: NO probe at construction; detection happens
    lazily on first use, guarded by hasattr(self, '_server_type')."""

    def __init__(self, *args):
        pass


class FakeEagerAuthorizer(object):
    """Mimics AccessTokenAuthorizer on python-tss-sdk <= 2.0.1: probes and
    sets _server_type eagerly in __init__, before anyone can intervene."""
    probes = 0

    def __init__(self, *args):
        FakeEagerAuthorizer.probes += 1
        self._server_type = 'detected_value'


class FakeServerTypeAwareAuthorizer(object):
    """Mimics the upcoming SDK (feature/server-detection): accepts a
    server_type= kwarg and skips probing entirely when it is supplied."""

    def __init__(self, *args, server_type=None):
        self.received_server_type = server_type
        if server_type is not None:
            self._server_type = server_type


@patch.multiple(TSS_IMPORT_PATH,
                HAS_TSS_SDK=True,
                SecretServerError=SecretServerError,
                SecretServer=RecordingSecretServer,
                AccessTokenAuthorizer=FakeEagerAuthorizer,
                PasswordGrantAuthorizer=FakeLazyAuthorizer,
                DomainPasswordGrantAuthorizer=FakeLazyAuthorizer)
class TestServerTypeOverride(TestCase):
    """ADO 734475 acceptance criterion: callers can DECLARE the server type
    so no detection probe is issued. Optional -- unset keeps the zero-config
    auto-detect + cache path untouched."""

    def setUp(self):
        tss._reset_cache()
        RecordingSecretServer.last_authorizer = None
        FakeEagerAuthorizer.probes = 0
        self.lookup = lookup_loader.get("delinea.platform_secretserver.tss")

    def tearDown(self):
        tss._reset_cache()
        RecordingSecretServer.last_authorizer = None
        FakeEagerAuthorizer.probes = 0

    def _run(self, **kwargs):
        run_kwargs = {'base_url': 'https://tenant.example.com',
                      'username': 'alice', 'password': 'p'}
        run_kwargs.update(kwargs)
        return self.lookup.run([1], [], **run_kwargs)

    def test_password_pin_skips_detection_probe(self):
        # Lazy authorizer + pre-pinned _server_type => the SDK's hasattr
        # guard sees it and never probes: 0 probes on today's SDK.
        self._run(server_type='platform')
        authorizer = RecordingSecretServer.last_authorizer
        self.assertIsInstance(authorizer, FakeLazyAuthorizer)
        self.assertEqual(authorizer._server_type, 'platform')

    def test_no_server_type_leaves_autodetect_untouched(self):
        self._run()
        authorizer = RecordingSecretServer.last_authorizer
        self.assertFalse(hasattr(authorizer, '_server_type'))

    def test_domain_pin_skips_detection_probe(self):
        self._run(server_type='secret_server', domain='corp')
        authorizer = RecordingSecretServer.last_authorizer
        self.assertEqual(authorizer._server_type, 'secret_server')

    def test_kwarg_passthrough_when_sdk_supports_it(self):
        with patch(make_absolute('PasswordGrantAuthorizer'),
                   FakeServerTypeAwareAuthorizer):
            self._run(server_type='platform')
        authorizer = RecordingSecretServer.last_authorizer
        self.assertEqual(authorizer.received_server_type, 'platform')
        self.assertEqual(authorizer._server_type, 'platform')

    def test_token_old_sdk_detected_value_stands(self):
        # AccessTokenAuthorizer <= 2.0.1 probes in __init__ before the pin
        # can act: the measured detection wins over the declared value (the
        # probe already happened; overriding a ground-truth result would
        # mis-route). The client cache bounds it to one probe per process.
        self._run(server_type='platform', token='tok',
                  username=None, password=None)
        authorizer = RecordingSecretServer.last_authorizer
        self.assertIsInstance(authorizer, FakeEagerAuthorizer)
        self.assertEqual(FakeEagerAuthorizer.probes, 1)
        self.assertEqual(authorizer._server_type, 'detected_value')

    def test_invalid_server_type_is_rejected(self):
        with self.assertRaises(tss.AnsibleError):
            self._run(server_type='bogus')

    def test_server_type_is_part_of_the_cache_key(self):
        # Same credentials with and without the override must not share a
        # client: the override changes endpoint routing.
        self._run()
        self._run(server_type='platform')
        self.assertEqual(len(tss._client_cache), 2)

    def test_v0_sdk_rejects_server_type(self):
        with patch(make_absolute('HAS_TSS_AUTHORIZER'), False):
            with self.assertRaises(tss.AnsibleError):
                self._run(server_type='platform')

    def test_uninspectable_signature_means_no_kwarg_passthrough(self):
        # If a class's signature cannot be inspected, treat it as not
        # supporting the kwarg (the attribute pin still applies).
        with patch(make_absolute('inspect')) as mock_inspect:
            mock_inspect.signature.side_effect = ValueError('no signature')
            self.assertFalse(
                tss._authorizer_accepts_server_type(FakeLazyAuthorizer))


def _real_response(status_code, body):
    response = MagicMock()
    response.status_code = status_code
    response.content = body
    return response


@unittest.skipUnless(HAS_REAL_SDK, 'python-tss-sdk not installed')
class TestRealSdkErrorContract(TestCase):
    """Drive errors through the REAL python-tss-sdk SecretServer.process()
    and assert the plugin's policy holds. These are the tests that catch a
    divergence between the SDK's actual error contract and what the plugin
    (and this file's test doubles) assume -- e.g. SDK <= 2.0.1 discarding
    the response object its errors are documented to carry."""

    def test_401_is_classified_safely_and_recovers_on_password_path(self):
        with self.assertRaises(RealSecretServerClientError) as ctx:
            RealSecretServer.process(
                _real_response(401, b'{"message": "token expired"}'))
        error = ctx.exception
        # must not crash regardless of which SDK version is installed
        tss._error_message(error)
        status = tss._response_status(error)
        # <= 2.0.1 discards the response (status None); a fixed SDK reports 401.
        # Either way the password path MAY retry once (the caller additionally
        # gates on the failing client having come from the cache) and the
        # token path never does.
        self.assertIn(status, (None, 401))
        self.assertTrue(tss._should_rebuild_and_retry(error, {'token': None}))
        self.assertFalse(tss._should_rebuild_and_retry(error, {'token': 'tok'}))

    def test_403_amplification_guard(self):
        with self.assertRaises(RealSecretServerClientError) as ctx:
            RealSecretServer.process(
                _real_response(403, b'{"message": "Forbidden"}'))
        error = ctx.exception
        status = tss._response_status(error)
        if status is None:
            # today's SDK: no status to classify -- the predicate allows the
            # password path one retry, but ONLY the caller's cache-hit gate
            # can actually trigger it (fresh builds -- the WAF-burst shape --
            # never retry), so the residual is a cached client's single shot
            self.assertTrue(tss._should_rebuild_and_retry(error, {'token': None}))
        else:
            # fixed SDK: 403 must never rebuild-and-retry
            self.assertEqual(status, 403)
            self.assertFalse(tss._should_rebuild_and_retry(error, {'token': None}))
        # the token path never retries under ANY SDK version
        self.assertFalse(tss._should_rebuild_and_retry(error, {'token': 'tok'}))

    def test_malformed_4xx_bodies_crash_or_raise_cleanly(self):
        # Documents the crashes _lookup_guarded exists for. A fixed SDK that
        # raises SecretServerError instead keeps both branches valid.
        for body in (b'{"foo": 1}', b'{"error": {"code": 5}}'):
            try:
                RealSecretServer.process(_real_response(400, body))
                self.fail('process() unexpectedly succeeded on a 400')
            except RealSecretServerClientError:
                pass  # fixed SDK: clean error
            except UnboundLocalError:
                pass  # <= 2.0.1: message local never bound; plugin guards this
        try:
            RealSecretServer.process(_real_response(400, b'123'))
            self.fail('process() unexpectedly succeeded on a 400')
        except RealSecretServerClientError:
            pass
        except TypeError:
            pass  # <= 2.0.1: non-dict JSON body; plugin guards this

    def test_real_error_str_repr_cannot_leak_credentials(self):
        # _error_message falls back to str(error)/repr(error): confirm the
        # real SDK's error carries nothing beyond the class name there.
        error = RealSecretServerClientError('msg', object())
        self.assertEqual(str(error), '')
        self.assertNotIn('msg', repr(error))
