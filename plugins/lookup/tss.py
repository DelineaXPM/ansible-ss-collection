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
"""

import abc
import os
import typing as t
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
    CacheKey = t.Tuple[
        t.Optional[str], t.Optional[str], t.Optional[str], t.Optional[str], t.Optional[str]
    ]


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
        try:
            return int(term)
        except ValueError as e:
            raise AnsibleOptionsError("Secret ID must be an integer") from e

    @staticmethod
    def _term_to_folder_id(term):
        try:
            return int(term)
        except ValueError as e:
            raise AnsibleOptionsError("Folder ID must be an integer") from e


class TSSClientV0(TSSClient):
    def __init__(self, **server_parameters):
        super().__init__()

        if server_parameters.get("domain"):
            raise AnsibleError("The 'domain' option requires 'python-tss-sdk' version 1.0.0 or greater")

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
        if server_parameters.get("token"):
            return AccessTokenAuthorizer(
                server_parameters["token"], server_parameters["base_url"]
            )

        if server_parameters.get("domain"):
            return DomainPasswordGrantAuthorizer(
                server_parameters["base_url"],
                server_parameters["username"],
                server_parameters["domain"],
                server_parameters["password"],
                server_parameters["token_path_uri"],
            )

        return PasswordGrantAuthorizer(
            server_parameters["base_url"],
            server_parameters["username"],
            server_parameters["password"],
            server_parameters["token_path_uri"],
        )


# Module-scope cache of TSSClient instances, keyed on credential identity.
# Each TSSClient holds a PasswordGrantAuthorizer whose internal token cache is
# only useful if the client is reused. Without this, every lookup() call mints
# a fresh /oauth2/token grant.
_client_cache: dict[CacheKey, TSSClient] = {}


def _credential_key(server_parameters: dict[str, str | None]) -> CacheKey | None:
    # token-based auth makes no /oauth2/token call, so caching adds nothing.
    if server_parameters.get("token"):
        return None
    # password is intentionally not part of the key: the cached client holds
    # the password as an instance attribute, so a second lookup with the
    # same username but a different password would not "fix" the cached
    # entry by being keyed separately - it would just split the cache and
    # the first authenticator's password is what actually gets used.
    return (
        server_parameters.get("base_url"),
        server_parameters.get("username"),
        server_parameters.get("domain"),
        server_parameters.get("api_path_uri"),
        server_parameters.get("token_path_uri"),
    )


def _get_or_build_client(server_parameters: dict[str, str | None]) -> TSSClient:
    key = _credential_key(server_parameters)
    if key is None:
        return TSSClient.from_params(**server_parameters)
    # On a cache miss, build the client (TSSClient.from_params makes the
    # /oauth2/token network call) and use setdefault to insert it. setdefault
    # resolves the case where two builds for the same key happen concurrently:
    # the first insert wins and the later client is discarded.
    tss = _client_cache.get(key)
    if tss is not None:
        return tss
    new_tss = TSSClient.from_params(**server_parameters)
    return _client_cache.setdefault(key, new_tss)


def _drop_cached_client(server_parameters: dict[str, str | None]) -> None:
    key = _credential_key(server_parameters)
    if key is None:
        return
    _client_cache.pop(key, None)


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
        }

        try:
            return self._lookup(terms, _get_or_build_client(params))
        except SecretServerError as error:
            # 4xx is often a stale cached token: the SDK's _refresh() adds the
            # drift instead of subtracting it, so a cached authorizer will keep
            # serving a token for ~5 minutes past server-side expiry. Drop the
            # cached client so the rebuild mints a fresh grant, and retry once.
            # 5xx and anything else propagate unchanged.
            if HAS_SS_CLIENT_ERROR and isinstance(error, SecretServerClientError):
                _drop_cached_client(params)
                # Retry re-runs _lookup for all terms, not just the one that
                # raised. A 4xx on term 3 of a 3-term lookup will re-fetch
                # terms 1 and 2 too. Correct (reads are idempotent) but worth
                # knowing if an audit log shows duplicate reads.
                try:
                    return self._lookup(terms, _get_or_build_client(params))
                except SecretServerError as retry_error:
                    raise AnsibleError(f"Secret Server lookup failure: {retry_error.message}") from retry_error
            raise AnsibleError(f"Secret Server lookup failure: {error.message}") from error

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
