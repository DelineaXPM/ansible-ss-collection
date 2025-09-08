# tss -- Get secrets from Delinea Secret server

## Synopsis

Uses the Delinea Secret Server Python SDK to get Secrets from a Secret Server _tenant_ using a access token or credentials (Username and Password).

## Requirements

The below requirements are needed on the host that executes this module.

- python-tss-sdk - https://pypi.org/project/python-tss-sdk/

## Parameters

\_terms (True, int, None)
The integer ID of the secret.

secret_path(False, str, None)
ndicate a full path of secret including folder and secret name when the secret ID is set to 0.

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

api_path_uri (False, any, /api/v1)
The path to append to the base URL to form a valid REST API request.

token_path_uri (False, any, "")
The path to append to the base URL to form a valid OAuth2 Access Grant request.

server_type (False, any, secret_server)
Define the server type used for authentication secret server or platform. secret_server server type is used for the Delinea Secret Server. platform server type is used for the Delinea Platform. This parameter is required only when accessing the secret using a platform token instead of user credentials.

## Examples

```yaml
# Using Secret Server Authentication
- hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.ss.tss',
                102,
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

- hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.ss.tss',
                102,
                base_url='https://secretserver.domain.com/SecretServer/',
                username='user.name',
                password='password',
                domain='domain'
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

- hosts: localhost
  vars:
      secret_password: >-
        {{
            ((lookup(
                'delinea.ss.tss',
                102,
                base_url='https://secretserver.domain.com/SecretServer/',
                token='delinea_access_token',
            )  | from_json).get('items') | items2dict(key_name='slug', value_name='itemValue'))['password']
        }}
  tasks:
      - ansible.builtin.debug:
          msg: the password is {{ secret_password }}

# Private key stores into certificate file which is attached with secret.
# If fetch_attachments=True then private key file will be download on specified path
# and file content will display in debug message.
- hosts: localhost
  vars:
      secret: >-
        {{
            lookup(
                'delinea.ss.tss',
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
                'delinea.ss.tss',
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
                'delinea.ss.tss',
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
                'delinea.ss.tss',
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
                'delinea.ss.tss',
                102,
                base_url='https://platform.delinea.app/',
                token='delinea_platform_access_token',
            )  | from_json).get('items') | items2dict(key_name='slug', value_name='itemValue'))['password']
        }}
  tasks:
      - name: Show password from secret
        ansible.builtin.debug:
            msg: the password is {{ secret_password }}
```

## Return Values

\_list (, list, )
One or more JSON responses to `GET /secrets/{id}` and `GET /secrets/{path}`.

## Status

## Authors

- Delinea (!UNKNOWN) (https://delinea.com/)
