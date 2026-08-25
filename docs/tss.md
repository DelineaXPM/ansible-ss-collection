# tss -- Get secrets from Delinea Secret server

## Synopsis

Uses the Delinea Secret Server Python SDK to get Secrets from a Secret Server _tenant_ using a access token or credentials (Username and Password).

## Requirements

The below requirements are needed on the host that executes this plugin.

- python-tss-sdk - https://pypi.org/project/python-tss-sdk/
- python-tss-sdk 2.0.1 or greater - required for OAuth2 token endpoint auto-detection, which an empty token_path_uri (the default) or token_path_source=auto relies on. Delinea Platform authentication needs auto-detection unless the Platform token path is pinned in token_path_uri explicitly.

## Parameters

\_terms (True, list, None)
The integer ID(s) of the secret(s) to retrieve, passed as positional arguments.

secret_path(False, str, None)
Indicate a full path of secret including folder and secret name when the secret ID is set to 0.

fetch_secret_ids_from_folder (False, bool, None)
Boolean flag which indicates whether secret ids are in a folder is fetched by folder ID or not. V(true) then the terms will be considered as a folder IDs. Otherwise (default), they are considered as secret IDs.

fetch_attachments (False, bool, None)
Boolean flag which indicates whether attached files will get downloaded or not. The download will only happen if O(file_download_path) has been provided.

file_download_path (False, path, None)
Indicate the file attachment download location.

base_url (True, any, None)
The base URL of the server, for example V(https://localhost/SecretServer).

username (True, any, None)
The username with which to request the OAuth2 Access Grant.

password (True, any, None)
The password associated with the supplied username. Required when O(token) is not provided.

domain (False, any, "")
The domain with which to request the OAuth2 Access Grant. Optional when O(token) is not provided. Requires C(python-tss-sdk) version 1.0.0 or greater.

token (True, any, None)
Existing token for Delinea authorizer. If provided, O(username) and O(password) are not needed. Requires C(python-tss-sdk) version 1.0.0 or greater.

server_type (False, str, None)
Explicitly declare whether O(base_url) is a V(secret_server) or a V(platform) tenant, instead of auto-detecting it via unauthenticated health-check probes. When set, username/password and domain authorizers issue no detection probes at all (token authorizers on current C(python-tss-sdk) releases still probe once per process). Leave unset for automatic detection. Use only when certain of the value - a wrong value routes the OAuth2 request to the wrong token endpoint and authentication fails.

api_path_uri (False, any, /api/v1)
The path to append to the base URL to form a valid REST API request.

token_path_uri (False, str, "")
The path to append to the base URL to form a valid OAuth2 Access Grant request. Leave empty (the default) to let python-tss-sdk auto-detect whether the host is Secret Server or the Delinea Platform and select the correct token endpoint; this is needed for Delinea Platform authentication with username and password unless the Platform token path (/identity/api/oauth2/token/xpmplatform) is pinned here explicitly. The empty default is a deliberate divergence from the community.general tss lookup (which defaults to /oauth2/token, the Secret Server-only path). Endpoint auto-detection requires python-tss-sdk version 2.0.1 or greater, which resolves an empty value to a fixed path per detected server type - /oauth2/token for Secret Server and /identity/api/oauth2/token/xpmplatform for the Delinea Platform. This option is used when token_path_source=token_path_uri (the default); token_path_source=auto ignores it and forces auto-detection.

token_path_source (False, str, token_path_uri)
How to determine the OAuth2 token endpoint path. Choices: token_path_uri (default) uses the token_path_uri option as given (which, with its empty default, already lets the SDK auto-detect the endpoint); auto ignores token_path_uri and always lets python-tss-sdk auto-detect the token endpoint from base_url, selecting the correct path for Secret Server or the Delinea Platform.

comment (False, str, None)
Optional comment to pass when retrieving the secret. This will be logged as an audit trail entry for secret access.

## Examples

```yaml
# Using Secret Server Authentication
- hosts: localhost
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
      - ansible.builtin.debug:
          msg: >
            the password is {{
              (secret['items']
                | items2dict(key_name='slug',
                             value_name='itemValue'))['password']
            }}

- hosts: localhost
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
      - ansible.builtin.debug:
          msg: >
            the password is {{
              (secret['items']
                | items2dict(key_name='slug',
                             value_name='itemValue'))['password']
            }}

- hosts: localhost
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
      - ansible.builtin.debug:
          msg: the password is {{ secret_password }}

# If "Require Comment" option is enabled under the Security tab of the secret in Secret Server,
# then the comment parameter must be provided when accessing the secret.
- hosts: localhost
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
      - ansible.builtin.debug:
          msg: >
            the password is {{
              (secret['items']
                | items2dict(key_name='slug',
                             value_name='itemValue'))['password']
            }}

# Private key stores into certificate file which is attached with secret.
# If fetch_attachments=True then private key file will be download on specified path
# and file content will display in debug message.
- hosts: localhost
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
    - ansible.builtin.debug:
        msg: >
          the private key is {{
            (secret['items']
              | items2dict(key_name='slug',
                           value_name='itemValue'))['private-key']
          }}

# If fetch_secret_ids_from_folder=true then secret IDs are in a folder is fetched based on folder ID
- hosts: localhost
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
    - ansible.builtin.debug:
        msg: >
          the secret id's are {{
              secret
          }}

# If secret ID is 0 and secret_path has value then secret is fetched by secret path
- hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.platform_secretserver.tss',
                0,
                secret_path='\folderName\secretName'
                base_url='https://secretserver.domain.com/SecretServer/',
                username='user.name',
                password='password'
            )
        }}
  tasks:
      - ansible.builtin.debug:
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
```

## Return Values

\_list (, list, )
One or more JSON responses to `GET /secrets/{id}` and `GET /secrets/{path}`.

## Status

## Authors

- Delinea (!UNKNOWN) (https://delinea.com/)
