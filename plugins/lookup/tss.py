# Copyright: (c) 2023, Delinea <https://delinea.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
name: tss
author: Delinea (!UNKNOWN) (https://delinea.com/)
short_description: Get secrets from Delinea Secret Server
version_added: 1.1.0
description:
    - Uses the Delinea Secret Server Python SDK to get Secrets from Secret
      Server using token authentication with O(username) and O(password) on
      the REST API at O(base_url).
    - When using self-signed certificates the environment variable
      E(REQUESTS_CA_BUNDLE) can be set to a file containing the trusted certificates
      (in C(.pem) format).
    - For example, C(export REQUESTS_CA_BUNDLE='/etc/ssl/certs/ca-bundle.trust.crt').
requirements:
    - python-tss-sdk - https://pypi.org/project/python-tss-sdk/
    - python-tss-sdk 2.0.1 or greater - required for OAuth2 token endpoint auto-detection, which an empty
      C(token_path_uri) (the default) or C(token_path_source=auto) relies on. Delinea Platform authentication
      needs auto-detection unless the Platform token path is pinned in C(token_path_uri) explicitly.
options:
    _terms:
        description: The integer ID(s) of the secret(s) to retrieve, passed as positional arguments.
        required: true
        type: list
        elements: int
    secret_path:
        description: Indicate a full path of secret including folder and secret name when the secret ID is set to 0.
        required: false
        type: str
    fetch_secret_ids_from_folder:
        description:
            - Boolean flag which indicates whether secret ids are in a folder is fetched by folder ID or not.
            - V(true) then the terms will be considered as a folder IDs. Otherwise (default), they are considered as secret IDs.
        required: false
        type: bool
    fetch_attachments:
        description:
            - Boolean flag which indicates whether attached files will get downloaded or not.
            - The download will only happen if O(file_download_path) has been provided.
        required: false
        type: bool
    file_download_path:
        description: Indicate the file attachment download location.
        required: false
        type: path
    base_url:
        description: The base URL of the server, for example V(https://localhost/SecretServer).
        env:
            - name: TSS_BASE_URL
        ini:
            - section: tss_lookup
              key: base_url
        required: true
    username:
        description: The username with which to request the OAuth2 Access Grant.
        env:
            - name: TSS_USERNAME
        ini:
            - section: tss_lookup
              key: username
    password:
        description:
            - The password associated with the supplied username.
            - Required when O(token) is not provided.
        env:
            - name: TSS_PASSWORD
        ini:
            - section: tss_lookup
              key: password
    domain:
        default: ""
        description:
          - The domain with which to request the OAuth2 Access Grant.
          - Optional when O(token) is not provided.
          - Requires C(python-tss-sdk) version 1.0.0 or greater.
        env:
            - name: TSS_DOMAIN
        ini:
            - section: tss_lookup
              key: domain
        required: false
    token:
        description:
          - Existing token for Delinea authorizer.
          - If provided, O(username) and O(password) are not needed.
          - Requires C(python-tss-sdk) version 1.0.0 or greater.
        env:
            - name: TSS_TOKEN
        ini:
            - section: tss_lookup
              key: token
    server_type:
        description:
          - Explicitly declare whether O(base_url) is a Secret Server or a
            Delinea Platform tenant, instead of auto-detecting it via
            unauthenticated health-check probes.
          - When set, username/password and domain authorizers issue V(0)
            detection probes. Token authorizers on current C(python-tss-sdk)
            releases (<= 2.0.1) detect eagerly at construction and still
            probe once per process; SDK versions whose authorizers accept a
            server type skip the probe on every path.
          - Leave unset for automatic detection (the default behavior).
          - Use only when certain of the value - a wrong value routes the
            OAuth2 request to the wrong token endpoint and authentication
            fails.
        type: str
        choices: [secret_server, platform]
        required: false
        env:
            - name: TSS_SERVER_TYPE
        ini:
            - section: tss_lookup
              key: server_type
        version_added: 1.4.0
    api_path_uri:
        default: /api/v1
        description: The path to append to the base URL to form a valid REST
            API request.
        env:
            - name: TSS_API_PATH_URI
        required: false
    token_path_uri:
        default: ""
        description:
            - The path to append to the base URL to form a valid OAuth2 Access Grant request.
            - Leave empty (the default) to let C(python-tss-sdk) auto-detect whether the host is Secret Server or the
              Delinea Platform and select the correct token endpoint. Set it explicitly (for example V(/oauth2/token))
              to pin a specific path.
            - Endpoint auto-detection requires C(python-tss-sdk) version 2.0.1 or greater, which resolves an empty value
              to a fixed path per detected server type - V(/oauth2/token) for Secret Server and
              V(/identity/api/oauth2/token/xpmplatform) for the Delinea Platform.
            - This option is used when O(token_path_source=token_path_uri) (the default). Setting O(token_path_source=auto)
              ignores this option and forces auto-detection regardless of the value here.
        type: str
        env:
            - name: TSS_TOKEN_PATH_URI
        ini:
            - section: tss_lookup
              key: token_path_uri
              version_added: 1.3.0
        required: false
    token_path_source:
        description:
            - How to determine the OAuth2 token endpoint path.
            - V(token_path_uri) uses the O(token_path_uri) option as given (which, with its empty default, already
              lets the SDK auto-detect the endpoint).
            - V(auto) ignores O(token_path_uri) and always lets C(python-tss-sdk) auto-detect the token endpoint from
              O(base_url), selecting the correct path for Secret Server or the Delinea Platform.
        type: str
        choices:
            - token_path_uri
            - auto
        default: token_path_uri
        env:
            - name: TSS_TOKEN_PATH_SOURCE
        ini:
            - section: tss_lookup
              key: token_path_source
        required: false
        version_added: 1.3.0
    comment:
        description:
          - Optional comment to pass when retrieving the secret.
          - This will be logged as an audit trail entry for secret access.
        required: false
        type: str
"""

RETURN = r"""
_list:
    description:
        - The JSON responses to C(GET /secrets/{id}) and C(GET /secrets/{path}).
    type: list
    elements: dict
"""

EXAMPLES = r"""
# Using Secret Server Authentication
- name: Lookup secret using Secret Server user credentials
  hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.platform_secretserver.tss',
                102,
                base_url='https://secretserver.domain.com/SecretServer/',
                username='user.name',
                password='password'
            ) | from_json
        }}
  tasks:
      - name: Show password from secret
        ansible.builtin.debug:
            msg: >
              the password is {{
                (secret['items']
                  | items2dict(key_name='slug',
                               value_name='itemValue'))['password']
              }}

- name: Lookup secret with domain user
  hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.platform_secretserver.tss',
                102,
                base_url='https://secretserver.domain.com/SecretServer/',
                username='user.name',
                password='password',
                domain='domain'
            ) | from_json
        }}
  tasks:
      - name: Show password from secret
        ansible.builtin.debug:
            msg: >
              the password is {{
                (secret['items']
                  | items2dict(key_name='slug',
                               value_name='itemValue'))['password']
              }}

- name: Lookup secret using Secret Server token
  hosts: localhost
  vars:
      secret_password: >-
        {{
            ((lookup(
                'delinea.platform_secretserver.tss',
                102,
                base_url='https://secretserver.domain.com/SecretServer/',
                token='delinea_access_token',
            )  | from_json).get('items') | items2dict(key_name='slug', value_name='itemValue'))['password']
        }}
  tasks:
      - name: Show password from secret
        ansible.builtin.debug:
            msg: the password is {{ secret_password }}

# If "Require Comment" option is enabled under the Security tab of the secret in Secret Server,
# then the comment parameter must be provided when accessing the secret.
- name: Lookup secret with comment for audit trail
  hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.platform_secretserver.tss',
                102,
                base_url='https://secretserver.domain.com/SecretServer/',
                username='user.name',
                password='password',
                comment='Accessed by Ansible for deployment'
            ) | from_json
        }}
  tasks:
      - name: Show password from secret
        ansible.builtin.debug:
            msg: >-
              the password is {{
                (secret['items']
                  | items2dict(key_name='slug',
                               value_name='itemValue'))['password']
              }}

# Private key stores into certificate file which is attached with secret.
# If fetch_attachments=True then private key file will be download on specified path
# and file content will display in debug message.
- name: Lookup secret and fetch attachments using Secret Server token
  hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.platform_secretserver.tss',
                102,
                fetch_attachments=True,
                file_download_path='/home/certs',
                base_url='https://secretserver.domain.com/SecretServer/',
                token='delinea_access_token'
            )
        }}
  tasks:
      - name: Show private key from secret
        ansible.builtin.debug:
            msg: >
              the private key is {{
                (secret['items']
                  | items2dict(key_name='slug',
                               value_name='itemValue'))['private-key']
              }}

# If fetch_secret_ids_from_folder=true then secret IDs are in a folder is fetched based on folder ID
- name: Lookup secret IDs by folder ID using Secret Server token
  hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.platform_secretserver.tss',
                102,
                fetch_secret_ids_from_folder=true,
                base_url='https://secretserver.domain.com/SecretServer/',
                token='delinea_access_token'
            )
        }}
  tasks:
      - name: Show secret IDs
        ansible.builtin.debug:
            msg: >
              the secret id's are {{
                  secret
              }}

# If secret ID is 0 and secret_path has value then secret is fetched by secret path
- name: Lookup secret by secret path using Secret Server user credentials
  hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.platform_secretserver.tss',
                0,
                secret_path='/folderName/secretName',
                base_url='https://secretserver.domain.com/SecretServer/',
                username='user.name',
                password='password'
            )
        }}
  tasks:
      - name: Show password from secret
        ansible.builtin.debug:
            msg: >
              the password is {{
                (secret['items']
                  | items2dict(key_name='slug',
                               value_name='itemValue'))['password']
              }}

# Using Platform Authentication
- name: Lookup secret using Platform service user credentials
  hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.platform_secretserver.tss',
                102,
                base_url='https://platform.delinea.app/',
                username='platform_service_username',
                password='platform_service_user_password'
            ) | from_json
        }}
  tasks:
      - name: Show password from secret
        ansible.builtin.debug:
            msg: >
              the password is {{
                (secret['items']
                  | items2dict(key_name='slug',
                               value_name='itemValue'))['password']
              }}

- name: Lookup secret using platform token
  hosts: localhost
  vars:
      secret_password: >-
        {{
            ((lookup(
                'delinea.platform_secretserver.tss',
                102,
                base_url='https://platform.delinea.app/',
                token='delinea_platform_access_token',
            )  | from_json).get('items') | items2dict(key_name='slug', value_name='itemValue'))['password']
        }}
  tasks:
      - name: Show password from secret
        ansible.builtin.debug:
            msg: the password is {{ secret_password }}

# Declaring the server type explicitly (skips health-check detection probes;
# useful behind a WAF-protected Platform tenant)
- name: Lookup secret declaring the server type
  hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.platform_secretserver.tss',
                102,
                base_url='https://platform.delinea.app/',
                username='platform_service_username',
                password='platform_service_user_password',
                server_type='platform'
            ) | from_json
        }}
  tasks:
      - name: Show password from secret
        ansible.builtin.debug:
            msg: >
              the password is {{
                (secret['items']
                  | items2dict(key_name='slug',
                               value_name='itemValue'))['password']
              }}
"""

import abc
import hashlib
import hmac
import inspect
import os
import secrets
import threading
import typing as t
from collections import OrderedDict
from ansible.errors import AnsibleError, AnsibleLookupError, AnsibleOptionsError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

try:
    from delinea.secrets.server import SecretServer, SecretServerError, PasswordGrantAuthorizer, DomainPasswordGrantAuthorizer, AccessTokenAuthorizer

    HAS_TSS_SDK = True
    HAS_DELINEA_SS_SDK = True
    HAS_TSS_AUTHORIZER = True
except ImportError:
    try:
        from thycotic.secrets.server import SecretServer, SecretServerError, PasswordGrantAuthorizer, DomainPasswordGrantAuthorizer, AccessTokenAuthorizer

        HAS_TSS_SDK = True
        HAS_DELINEA_SS_SDK = False
        HAS_TSS_AUTHORIZER = True
    except ImportError:
        SecretServer = None
        SecretServerError = None
        HAS_TSS_SDK = False
        HAS_DELINEA_SS_SDK = False
        PasswordGrantAuthorizer = None
        DomainPasswordGrantAuthorizer = None
        AccessTokenAuthorizer = None
        HAS_TSS_AUTHORIZER = False

# SecretServerClientError (4xx) is exported in newer SDK builds. When present
# it lets us distinguish auth/permission failures from 5xx service errors so
# we can invalidate a stale cached client and retry once.
try:
    from delinea.secrets.server import SecretServerClientError
    HAS_SS_CLIENT_ERROR = True
except ImportError:
    try:
        from thycotic.secrets.server import SecretServerClientError
        HAS_SS_CLIENT_ERROR = True
    except ImportError:
        SecretServerClientError = None
        HAS_SS_CLIENT_ERROR = False


if t.TYPE_CHECKING:
    # PEP 604 (``str | None``) is valid in annotations here via
    # ``from __future__ import annotations``, but a type *alias* is a runtime
    # assignment, so it uses the typing forms to stay valid for mypy on this
    # collection's Python 3.9 floor. Equivalent to community.general's
    # ``tuple[str | None, ...]``.
    CacheKey = t.Tuple[t.Optional[str], ...]


display = Display()


def check_for_wrong_terms(plugin, *, direct):
    # Vendored from community.general's plugin_utils._lookup (cannot import that
    # private module from another collection): reject terms passed via the
    # unsupported ``_terms=`` keyword and point users at positional arguments.
    # The single-element loop intentionally mirrors upstream's multi-keyword
    # guard shape so this vendored copy stays easy to diff against community.general.
    for opt in ("_terms",):
        if opt in direct:
            raise AnsibleLookupError(
                f"The {opt!r} keyword argument is not supported, you must provide terms as positional arguments: use"
                f" lookup({plugin.ansible_name!r}, arg1, arg2) instead of lookup({plugin.ansible_name!r}, {opt}=[arg1, arg2])"
            )


class TSSClient(metaclass=abc.ABCMeta):  # noqa: B024
    def __init__(self):
        self._client = None

    @staticmethod
    def from_params(**server_parameters):
        if HAS_TSS_AUTHORIZER:
            return TSSClientV1(**server_parameters)
        else:
            return TSSClientV0(**server_parameters)

    def get_secret(self, term, secret_path, fetch_file_attachments, file_download_path, comment=None):
        display.debug(f"tss_lookup term: {term}")
        secret_id = self._term_to_secret_id(term)
        if secret_id == 0 and secret_path:
            fetch_secret_by_path = True
            display.vvv(f"Secret Server lookup of Secret with path {secret_path}")
        else:
            fetch_secret_by_path = False
            display.vvv(f"Secret Server lookup of Secret with ID {secret_id}")

        query_params = None
        if comment:
            query_params = {"autoComment": comment}

        if fetch_file_attachments:
            if fetch_secret_by_path:
                obj = self._client.get_secret_by_path(secret_path, fetch_file_attachments)
            else:
                obj = self._client.get_secret(secret_id, fetch_file_attachments, query_params)
            for i in obj["items"]:
                if file_download_path and os.path.isdir(file_download_path):
                    if i["isFile"]:
                        try:
                            file_content = i["itemValue"].content
                            with open(os.path.join(file_download_path, f"{obj['id']}_{i['slug']}"), "wb") as f:
                                f.write(file_content)
                        except ValueError as e:
                            raise AnsibleOptionsError(f"Failed to download {i['slug']}") from e
                        except AttributeError:
                            display.warning(f"Could not read file content for {i['slug']}")
                        finally:
                            i["itemValue"] = "*** Not Valid For Display ***"
                else:
                    raise AnsibleOptionsError("File download path does not exist")
            return obj
        else:
            if fetch_secret_by_path:
                return self._client.get_secret_by_path(secret_path, False)
            else:
                return self._client.get_secret_json(secret_id, query_params)

    def get_secret_ids_by_folderid(self, term):
        display.debug(f"tss_lookup term: {term}")
        folder_id = self._term_to_folder_id(term)
        display.vvv(f"Secret Server lookup of Secret id's with Folder ID {folder_id}")

        return self._client.get_secret_ids_by_folderid(folder_id)

    @staticmethod
    def _term_to_secret_id(term):
        # TypeError too (term=None from an undefined variable, term=dict from
        # a bad template): it must surface as a caller-side options error,
        # not get misattributed to the server by _lookup_guarded.
        try:
            return int(term)
        except (ValueError, TypeError) as e:
            raise AnsibleOptionsError("Secret ID must be an integer") from e

    @staticmethod
    def _term_to_folder_id(term):
        try:
            return int(term)
        except (ValueError, TypeError) as e:
            raise AnsibleOptionsError("Folder ID must be an integer") from e


def _authorizer_accepts_server_type(authorizer_class):
    # The upcoming python-tss-sdk exposes a server_type= constructor kwarg
    # that skips health-probe detection natively. Feature-detect it so the
    # lookup option upgrades from "pin the attribute" to "real kwarg" the
    # moment users install that SDK -- no collection change needed.
    try:
        return "server_type" in inspect.signature(authorizer_class.__init__).parameters
    except (TypeError, ValueError):
        return False


def _build_authorizer(authorizer_class, args, server_type):
    if server_type and _authorizer_accepts_server_type(authorizer_class):
        authorizer = authorizer_class(*args, server_type=server_type)
    else:
        authorizer = authorizer_class(*args)
    if server_type and not hasattr(authorizer, "_server_type"):
        # Lazy-detecting authorizers (password/domain on python-tss-sdk
        # <= 2.0.1) probe on first use behind a hasattr(self, "_server_type")
        # guard -- pre-pinning the attribute means the health probes are
        # never issued. Eager ones (token on <= 2.0.1) have already detected
        # by the time construction returns; the measured result stands, since
        # overriding ground truth would mis-route the vault URL selection.
        authorizer._server_type = server_type
    return authorizer


class TSSClientV0(TSSClient):
    def __init__(self, **server_parameters):
        super().__init__()

        if server_parameters.get("domain"):
            raise AnsibleError("The 'domain' option requires 'python-tss-sdk' version 1.0.0 or greater")

        if server_parameters.get("server_type"):
            raise AnsibleError("The 'server_type' option requires 'python-tss-sdk' version 1.0.0 or greater")

        self._client = SecretServer(
            server_parameters["base_url"],
            server_parameters["username"],
            server_parameters["password"],
            server_parameters["api_path_uri"],
            server_parameters["token_path_uri"],
        )


class TSSClientV1(TSSClient):
    def __init__(self, **server_parameters):
        super().__init__()

        authorizer = self._get_authorizer(**server_parameters)
        self._client = SecretServer(
            server_parameters["base_url"], authorizer, server_parameters["api_path_uri"]
        )

    @staticmethod
    def _get_authorizer(**server_parameters):
        server_type = server_parameters.get("server_type")

        if server_parameters.get("token"):
            return _build_authorizer(
                AccessTokenAuthorizer,
                (server_parameters["token"], server_parameters["base_url"]),
                server_type,
            )

        if server_parameters.get("domain"):
            return _build_authorizer(
                DomainPasswordGrantAuthorizer,
                (
                    server_parameters["base_url"],
                    server_parameters["username"],
                    server_parameters["domain"],
                    server_parameters["password"],
                    server_parameters["token_path_uri"],
                ),
                server_type,
            )

        return _build_authorizer(
            PasswordGrantAuthorizer,
            (
                server_parameters["base_url"],
                server_parameters["username"],
                server_parameters["password"],
                server_parameters["token_path_uri"],
            ),
            server_type,
        )


# Module-scope cache of TSSClient instances, keyed on credential identity.
# Reuse is what makes lookups cheap on the network: AccessTokenAuthorizer
# eagerly probes the health-check endpoints at construction to detect the
# server type, and PasswordGrantAuthorizer (construction itself is free)
# holds the /oauth2/token access grant it mints lazily on first use -- a
# grant only reuse can preserve. Without this cache, every lookup() call
# repeats that work -- and against a Delinea Platform tenant the resulting
# /health burst trips the edge WAF rate limit (ADO 734475). Bounded LRU:
# hits refresh recency, inserts beyond the bound evict the
# least-recently-used entry.
_client_cache: OrderedDict[CacheKey, TSSClient] = OrderedDict()
# The lock guards invariants a plain dict never had: the LRU bookkeeping
# spans several statements (get + move_to_end, setdefault + move_to_end +
# popitem), so it is not atomic the way a single dict operation is.
_client_cache_lock = threading.Lock()
_CLIENT_CACHE_MAXSIZE = 128

# Per-process random key for token-derived cache keys. A cache key must not
# BE a credential: HMAC-SHA256(key, token) is one-way, immune to
# length-extension by construction, and the per-process random key means the
# digest cannot be precomputed offline nor correlated across processes if it
# ever leaks (traceback, debugger, core dump).
_KEY_SALT = secrets.token_bytes(32)


def _credential_key(server_parameters: dict[str, str | None]) -> CacheKey:
    token = server_parameters.get("token")
    if token:
        # Token auth builds an AccessTokenAuthorizer whose __init__ probes
        # /api/v1/healthcheck + /health eagerly, so caching matters MOST on
        # this path. Key on a keyed digest of the token, never the token.
        return (
            "token",
            server_parameters.get("base_url"),
            server_parameters.get("api_path_uri"),
            server_parameters.get("server_type"),
            hmac.new(_KEY_SALT, token.encode("utf-8"), hashlib.sha256).hexdigest(),
        )
    # password is intentionally not part of the key: the cached client holds
    # the password as an instance attribute, so a second lookup with the
    # same username but a different password would not "fix" the cached
    # entry by being keyed separately - it would just split the cache and
    # the first authenticator's password is what actually gets used.
    return (
        "password",
        server_parameters.get("base_url"),
        server_parameters.get("username"),
        server_parameters.get("domain"),
        server_parameters.get("api_path_uri"),
        server_parameters.get("token_path_uri"),
        server_parameters.get("server_type"),
    )


def _get_or_build_client(server_parameters: dict[str, str | None]) -> tuple[TSSClient, bool]:
    """Return ``(client, from_cache)``.

    ``from_cache`` is the retry gate: only a client that was REUSED from the
    cache can be carrying a stale token (the SDK's _refresh() drift bug), so
    only errors from a cached client justify a rebuild-and-retry. A freshly
    built client that fails cannot be fixed by building it again -- and in
    the fork-per-host burst that trips the Platform WAF every worker starts
    with an empty cache, so gating on this drops retry amplification there
    to zero (ADO 734475).
    """
    key = _credential_key(server_parameters)
    # Check under the lock first; if we miss, build the client outside the
    # lock (TSSClient.from_params makes network calls) and then use
    # setdefault to insert atomically. A racing thread that built the same
    # key first wins; we drop our just-built client on the floor.
    with _client_cache_lock:
        tss = _client_cache.get(key)
        if tss is not None:
            _client_cache.move_to_end(key)
    if tss is not None:
        return tss, True
    display.vvv(
        "delinea.platform_secretserver tss lookup: client cache miss;"
        f" building TSSClient (auth={key[0]},"
        f" base_url={server_parameters.get('base_url')})"
    )
    new_tss = TSSClient.from_params(**server_parameters)
    evicted = 0
    with _client_cache_lock:
        cached = _client_cache.setdefault(key, new_tss)
        # Refresh recency whether we won the insert race or lost it -- the
        # losing thread's traffic should still count toward LRU recency.
        _client_cache.move_to_end(key)
        while len(_client_cache) > _CLIENT_CACHE_MAXSIZE:
            _client_cache.popitem(last=False)
            evicted += 1
    if evicted:
        # Visible thrash signal: if this fires on every lookup, the process
        # cycles more credential identities than the bound and the probe
        # burst is back -- raise _CLIENT_CACHE_MAXSIZE or split the run.
        entries = "entry" if evicted == 1 else "entries"
        display.vvv(
            "delinea.platform_secretserver tss lookup: client cache evicted"
            f" {evicted} least-recently-used {entries}"
            f" (bound={_CLIENT_CACHE_MAXSIZE})"
        )
    # A race loser also reports from_cache=False: the winner built the
    # client moments ago, so a stale token is just as impossible.
    return cached, False


def _reset_cache() -> None:
    with _client_cache_lock:
        _client_cache.clear()


def _drop_cached_client(server_parameters: dict[str, str | None]) -> None:
    key = _credential_key(server_parameters)
    with _client_cache_lock:
        _client_cache.pop(key, None)


def _response_status(error):
    # python-tss-sdk <= 2.0.1 DISCARDS the requests.Response when it builds
    # SecretServerError (its __init__ accepts ``response`` but never stores
    # it), so with today's SDK this returns None for every error. The
    # attribute read is kept for SDKs that do expose it (the upstream fix for
    # ADO 734475 adds ``self.response = response``); until then callers must
    # treat None as "status unknown", not as an error shape.
    return getattr(getattr(error, "response", None), "status_code", None)


def _error_message(error):
    # .message is whatever the server's JSON body carried -- it is not
    # guaranteed to be a string (a structured {"message": {...}} body comes
    # through as a dict). Never let that crash error handling.
    message = getattr(error, "message", None)
    if message is None or message == "":
        return str(error) or repr(error)
    if not isinstance(message, str):
        return str(message)
    return message


def _sanitize_server_text(text):
    # Server-controlled text is echoed into controller logs: strip control
    # characters (ANSI escapes, DEL, etc.) and bound the length.
    cleaned = "".join(ch for ch in text if (ch >= " " and ch != "\x7f") or ch == "\t")
    if len(cleaned) > 200:
        cleaned = cleaned[:200] + "..."
    return cleaned


# Substrings that mark a 400 as a credential-expiry response. Anchored to
# OAuth error codes -- a bare "expired" would match unrelated server text
# ("password expired", "the secret has expired") and force futile rebuilds.
_STALE_TOKEN_MARKERS = ("invalid_grant", "invalid_token", "token_expired", "expired_token")


def _should_rebuild_and_retry(error, server_parameters):
    """Decide whether dropping the cached client and retrying once can help.

    Never for token auth: AccessTokenAuthorizer re-presents the same static
    token, so a rebuild cannot mint a new credential -- it just fires an
    extra health-probe pair for a retry that is guaranteed to fail the same
    way (ADO 734475).

    For password/domain auth the rebuild mints a fresh OAuth grant, which
    recovers the common stale-cached-token case (the SDK's _refresh() drift
    bug serves a token ~5 minutes past server-side expiry). Note the caller
    additionally gates on the failing client having come FROM the cache --
    a fresh build cannot hold a stale token (see _get_or_build_client):

    - status unknown (python-tss-sdk <= 2.0.1 discards the response, see
      _response_status): retry once. Reachable only on a cache hit, and
      single-shot, so a WAF 403 burst is amplified at most 2x and never
      unbounded; losing the retry entirely would regress stale-token
      recovery to a hard failure.
    - 401: retry once.
    - 400 with an OAuth invalid/expired-token marker: retry once.
    - 403/429 and everything else: never. They signal an authorization
      denial or the Platform edge WAF rate limit, and rebuilding amplifies
      the very burst that got the source IP blocked.
    """
    if server_parameters.get("token"):
        return False
    status = _response_status(error)
    if status is None:
        return True
    if status == 401:
        return True
    if status == 400:
        message = _error_message(error).lower()
        return any(marker in message for marker in _STALE_TOKEN_MARKERS)
    return False


def _format_lookup_failure(error):
    message = f"Secret Server lookup failure: {_sanitize_server_text(_error_message(error))}"
    status = _response_status(error)
    if status is None and "health check" in _error_message(error).lower():
        # The SDK's server-type detection probes /api/v1/healthcheck and
        # /health at authorizer construction; when both fail there is no
        # status to report. Against a Platform tenant this is the signature
        # of the edge WAF rate-limiting the probe burst (ADO 734475), so say
        # so -- this is the most likely user-facing message for that
        # condition.
        message += (
            " (The server-type probe could not reach /api/v1/healthcheck or"
            " /health. Against a Delinea Platform tenant this is commonly"
            " the edge WAF rate limit blocking the probe burst; throttle the"
            " play with serial:/forks: and retry.)"
        )
    if status in (403, 429):
        message += (
            f" (HTTP {status}: not retrying. If this occurs in bursts against a"
            " Delinea Platform tenant, it is likely the edge WAF rate limit;"
            " retrying would amplify the burst."
        )
        headers = getattr(getattr(error, "response", None), "headers", None) or {}
        retry_after = headers.get("Retry-After")
        if retry_after:
            message += f" The server sent Retry-After: {retry_after}."
        message += ")"
    return message


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        if not HAS_TSS_SDK:
            raise AnsibleError("python-tss-sdk must be installed to use this plugin")

        self.set_options(var_options=variables, direct=kwargs)
        check_for_wrong_terms(self, direct=kwargs)

        # token_path_uri defaults to "" (see DOCUMENTATION) on purpose: an empty
        # value lets python-tss-sdk auto-detect Secret Server vs the Delinea
        # Platform and pick the correct token endpoint. Do NOT change the default
        # to community.general's "/oauth2/token" - that is Secret-Server-only and
        # breaks Delinea Platform authentication.
        # token_path_source=auto forces that auto-detection even when token_path_uri
        # has been set to an explicit path.
        token_path_uri = self.get_option("token_path_uri")
        if self.get_option("token_path_source") == "auto":
            token_path_uri = ""

        params = {
            "base_url": self.get_option("base_url"),
            "username": self.get_option("username"),
            "password": self.get_option("password"),
            "domain": self.get_option("domain"),
            "token": self.get_option("token"),
            "api_path_uri": self.get_option("api_path_uri"),
            "token_path_uri": token_path_uri,
            "server_type": self.get_option("server_type"),
        }

        from_cache = False
        try:
            client, from_cache = _get_or_build_client(params)
            return self._lookup_guarded(terms, client)
        except SecretServerError as error:
            # A stale cached token (the SDK's _refresh() adds the drift
            # instead of subtracting it, so a cached authorizer keeps serving
            # a token ~5 minutes past server-side expiry) surfaces as a client
            # error. Drop the cached client so the rebuild mints a fresh
            # grant, and retry once -- but ONLY when the failing client came
            # from the cache: a fresh build cannot hold a stale token, so
            # retrying it just doubles traffic against a possibly WAF-blocked
            # tenant (ADO 734475). See _should_rebuild_and_retry for the rest
            # of the policy (token auth never retries; 403/429 never retry).
            # 5xx and anything else propagate unchanged.
            if (
                HAS_SS_CLIENT_ERROR
                and isinstance(error, SecretServerClientError)
                and from_cache
                and _should_rebuild_and_retry(error, params)
            ):
                _drop_cached_client(params)
                # Retry re-runs _lookup for all terms, not just the one that
                # raised. A stale-token error on term 3 of a 3-term lookup
                # will re-fetch terms 1 and 2 too. Correct (reads are
                # idempotent) but worth knowing if an audit log shows
                # duplicate reads.
                try:
                    retry_client, _dummy = _get_or_build_client(params)
                    return self._lookup_guarded(terms, retry_client)
                except SecretServerError as retry_error:
                    raise AnsibleError(_format_lookup_failure(retry_error)) from retry_error
            raise AnsibleError(_format_lookup_failure(error)) from error

    def _lookup_guarded(self, terms, tss):
        # python-tss-sdk <= 2.0.1 SecretServer.process() crashes instead of
        # raising SecretServerError when a 4xx JSON body lacks the keys it
        # expects: {"foo": 1} leaves its ``message`` local unbound
        # (UnboundLocalError) and a non-dict JSON body ({"error": 5}, "123")
        # raises TypeError. Surface those as clean lookup failures instead of
        # letting a raw traceback escape to the controller.
        try:
            return self._lookup(terms, tss)
        except (UnboundLocalError, TypeError) as error:
            detail = _sanitize_server_text(str(error))
            suffix = f": {detail}" if detail else ""
            raise AnsibleError(
                "Secret Server lookup failure: the server returned a"
                f" malformed error response ({type(error).__name__}{suffix})"
            ) from error

    def _lookup(self, terms, tss):
        if self.get_option("fetch_secret_ids_from_folder"):
            if HAS_DELINEA_SS_SDK:
                return [tss.get_secret_ids_by_folderid(term) for term in terms]
            raise AnsibleError("latest python-tss-sdk must be installed to use this plugin")
        return [
            tss.get_secret(
                term,
                self.get_option("secret_path"),
                self.get_option("fetch_attachments"),
                self.get_option("file_download_path"),
                self.get_option("comment"),
            )
            for term in terms
        ]
