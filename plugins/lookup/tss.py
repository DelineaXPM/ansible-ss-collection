# -*- coding: utf-8 -*-
# Copyright: (c) 2023, Delinea <https://delinea.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

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
options:
    _terms:
        description: The integer ID of the secret.
        required: true
        type: int
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
        description:
            - Indicate the file attachment download location.
            - Each attachment is staged in this directory and moved into place
              only once it has been written in full, so a failed download
              leaves any file from a previous run untouched.
            - Every download is treated as a new file and is given the
              permissions a plain file creation would produce, so the mode of
              a file left by a previous run is replaced, not inherited.
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
        description: The path to append to the base URL to form a valid OAuth2
            Access Grant request.
        env:
            - name: TSS_TOKEN_PATH_URI
        required: false
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
            )
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
import tempfile
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils import six
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


display = Display()


@six.add_metaclass(abc.ABCMeta)
class TSSClient(object):
    def __init__(self):
        self._client = None

    @staticmethod
    def from_params(**server_parameters):
        if HAS_TSS_AUTHORIZER:
            return TSSClientV1(**server_parameters)
        else:
            return TSSClientV0(**server_parameters)

    def get_secret(self, term, secret_path, fetch_file_attachments, file_download_path, comment=None):
        display.debug("tss_lookup term: %s" % term)
        secret_id = self._term_to_secret_id(term)
        if secret_id == 0 and secret_path:
            fetch_secret_by_path = True
            display.vvv(u"Secret Server lookup of Secret with path %s" % secret_path)
        else:
            fetch_secret_by_path = False
            display.vvv(u"Secret Server lookup of Secret with ID %d" % secret_id)

        query_params = None
        if comment:
            query_params = {'autoComment': comment}

        if fetch_file_attachments:
            if fetch_secret_by_path:
                obj = self._client.get_secret_by_path(secret_path, fetch_file_attachments)
            else:
                obj = self._client.get_secret(secret_id, fetch_file_attachments, query_params)

            if not (file_download_path and os.path.isdir(file_download_path)):
                raise AnsibleOptionsError("File download path does not exist")

            for i in obj['items']:
                if not i['isFile']:
                    continue
                try:
                    self._download_file_attachment(obj, i, file_download_path)
                finally:
                    i['itemValue'] = "*** Not Valid For Display ***"
            return obj
        else:
            if fetch_secret_by_path:
                return self._client.get_secret_by_path(secret_path, False)
            else:
                return self._client.get_secret_json(secret_id, query_params)

    def _download_file_attachment(self, secret, item, file_download_path):
        """Write a single file attachment to ``file_download_path``.

        Failures are reported and propagated instead of being reduced to a
        warning: an attachment that is quietly absent looks to the playbook
        like a successful run, and the task that consumes the file fails
        later with no indication of why the file is not there.
        """
        slug = str(item['slug'])
        destination = os.path.join(
            file_download_path, "{0}_{1}".format(secret['id'], slug)
        )

        if not item.get('fileAttachmentId'):
            display.warning(
                u"Secret Server item '%s' of secret %s is a file field with no "
                u"attachment; nothing was written to %s"
                % (slug, secret['id'], destination)
            )
            return

        try:
            # requests.RequestException derives from OSError, so a connection
            # that drops while the body is read lands in the second handler.
            file_content = item['itemValue'].content
        except AttributeError:
            raise AnsibleError(
                "Failed to download attachment '{0}' of secret {1}: Secret Server "
                "returned no file content for attachment {2}".format(
                    slug, secret['id'], item['fileAttachmentId']
                )
            )
        except (ValueError, OSError) as error:
            raise AnsibleError(
                "Failed to download attachment '{0}' of secret {1}: {2}".format(
                    slug, secret['id'], error
                )
            )

        try:
            self._write_file_atomically(destination, file_content)
        except (TypeError, ValueError, OSError) as error:
            raise AnsibleError(
                "Failed to write attachment '{0}' of secret {1} to {2}: "
                "{3}".format(slug, secret['id'], destination, error)
            )

        display.vvv(
            u"Secret Server wrote attachment '%s' of secret %s to %s"
            % (slug, secret['id'], destination)
        )

    @staticmethod
    def _write_file_atomically(destination, content):
        """Replace ``destination`` with ``content``, or leave it as it was.

        Opening the destination directly in C(wb) mode truncates it before the
        content is known to be readable and writable, so a download that fails
        part way through destroys the file a previous run left behind. Staging
        in the destination directory keeps the final move atomic.
        """
        directory = os.path.dirname(destination) or "."
        mode = TSSClient._new_file_mode()
        handle, temp_path = tempfile.mkstemp(
            dir=directory, prefix=".tss-", suffix=".part"
        )
        replaced = False

        try:
            with os.fdopen(handle, "wb") as temp_file:
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.chmod(temp_path, mode)
            os.replace(temp_path, destination)
            replaced = True
        finally:
            if not replaced:
                TSSClient._remove_quietly(temp_path)

    @staticmethod
    def _new_file_mode():
        """Permissions to give the staged attachment.

        Every download is treated as a new file, so the mode a plain
        ``open()`` would have produced is applied and the mode of whatever
        was at the destination is not inherited. That keeps repeated runs
        predictable, and stops ``mkstemp``'s own ``0600`` from silently
        tightening a file other accounts read today.
        """
        umask = os.umask(0)
        os.umask(umask)
        return 0o666 & ~umask

    @staticmethod
    def _remove_quietly(path):
        try:
            os.remove(path)
        except OSError as error:
            display.warning(
                u"Could not remove temporary file %s: %s" % (path, error)
            )

    def get_secret_ids_by_folderid(self, term):
        display.debug("tss_lookup term: %s" % term)
        folder_id = self._term_to_folder_id(term)
        display.vvv(u"Secret Server lookup of Secret id's with Folder ID %d" % folder_id)

        return self._client.get_secret_ids_by_folderid(folder_id)

    @staticmethod
    def _term_to_secret_id(term):
        try:
            return int(term)
        except ValueError:
            raise AnsibleOptionsError("Secret ID must be an integer")

    @staticmethod
    def _term_to_folder_id(term):
        try:
            return int(term)
        except ValueError:
            raise AnsibleOptionsError("Folder ID must be an integer")


class TSSClientV0(TSSClient):
    def __init__(self, **server_parameters):
        super(TSSClientV0, self).__init__()

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
        super(TSSClientV1, self).__init__()

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


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        if not HAS_TSS_SDK:
            raise AnsibleError("python-tss-sdk must be installed to use this plugin")

        self.set_options(var_options=variables, direct=kwargs)

        tss = TSSClient.from_params(
            base_url=self.get_option("base_url"),
            username=self.get_option("username"),
            password=self.get_option("password"),
            domain=self.get_option("domain"),
            token=self.get_option("token"),
            api_path_uri=self.get_option("api_path_uri"),
            token_path_uri=self.get_option("token_path_uri")
        )

        try:
            if self.get_option("fetch_secret_ids_from_folder"):
                if HAS_DELINEA_SS_SDK:
                    return [tss.get_secret_ids_by_folderid(term) for term in terms]
                else:
                    raise AnsibleError("latest python-tss-sdk must be installed to use this plugin")
            else:
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
        except SecretServerError as error:
            raise AnsibleError(
                "Secret Server lookup failure: %s" % self._format_sdk_error(error)
            )

    @staticmethod
    def _format_sdk_error(error):
        """Render a C(SecretServerError) as a message worth logging.

        C(SecretServerServiceError) is built with the ``requests`` response as
        its message, which otherwise reaches the user as C(<Response [500]>).
        """
        message = getattr(error, "message", None)
        if message is None:
            return str(error) or error.__class__.__name__

        status_code = getattr(message, "status_code", None)
        if status_code is None:
            return str(message)

        body = (getattr(message, "text", "") or "").strip()
        if body:
            return "HTTP %s: %s" % (status_code, body[:512])
        return "HTTP %s" % status_code
