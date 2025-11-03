# Development Guide

Table of contents:

- [Prerequisites](#prerequisites)
- [Get the code](#get-the-code)
- [Development](#development)
- [Release](#release)

Make sure to checkout [the official developer guide for developing collections][developing-collections].

## Prerequisites

- [Python][get-python] version 3.7 or higher
- [pytest][get-pytest]
- [python-tss-sdk][get-sdk]

## Get the code

Ansible requires that collections are stored in `{...}/ansible_collections/NAMESPACE/COLLECTION_NAME` path.
Therefore to be able to run tests, clone this repository to `{arbitrary path}/ansible_collections/delinea/platform_secretserver`.

Example with using home directory:

```shell
mkdir -p ~/ansible_collections/delinea/platform_secretserver
```

```shell
git clone git@github.com:DelineaXPM/ansible-ss-collection.git ~/ansible_collections/delinea/platform_secretserver
```

```shell
cd ~/ansible_collections/delinea/platform_secretserver
```

## Development
Create a new virtual environment

```shell
python3 -m venv env
source env/bin/activate
```

Install Ansible:

```shell
sudo apt update
sudo apt install ansible
```

Build Ansible Collection:

```shell
ansible-galaxy collection build --force
```

Run sanity tests:

```shell
ansible-test sanity
```

Run unit tests:

```shell
python3 -m pytest
```

Install and Run Ansible Lint:

```shell
pip3 install ansible-lint
ansible-lint
```

Install Ansible Collection locally

```shell
ansible-galaxy collection install delinea-platform_secretserver-1.0.0.tar.gz --force
```

Test Ansble collection plugin

```shell
ansible-playbook playbook.yml
```

## Release

Follow [this link][delinea-platform_secretserver-galaxy] to open the `delinea.platform_secretserver` collection in [Ansible Galaxy][galaxy] hub.

1. Change the version number. Follow semantic versioning when setting the version for your collection:

    * Increment the major version number, x of x.y.z, for an incompatible API change.
    * Increment the minor version number, y of x.y.z, for new functionality in a backwards compatible manner (for example new modules/plugins, parameters, return values).
    * Increment the patch version number, z of x.y.z, for backwards compatible bug fixes.

2. Update installation instructions in [README.md][readme.md].

3. Write a release summary:

    Add [version_number].yml file under changelogs/fragment folder and write release summary in below format:

    ```shell
    release_summary: `<describe release summary>`
    ```

    Then generate changelog using below commands

   ```shell
   pip install antsibull-changelog
   antsibull-changelog init <path/to/your/collection>
   antsibull-changelog release [--version version_number]
   ```

4. Build the collection:

   ```shell
   ansible-galaxy collection build --force
   ```

   As a result a new archive will be generated (e.g. `delinea-platform_secretserver-1.0.0.tar.gz`) in the collection directory (`~/ansible_collections/delinea/platform_secretserver/`).

5. Publish the collection:

   ```shell
   ansible-galaxy collection publish ~/ansible_collections/delinea/platform_secretserver/delinea-platform_secretserver-1.0.0.tar.gz -api-key=SECRET
   ```

[developing-collections]: https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html
[get-python]: https://www.python.org/downloads/
[get-pytest]: https://docs.pytest.org/en/7.1.x/getting-started.html#install-pytest
[get-sdk]: https://pypi.org/project/python-tss-sdk/
[delinea-core-galaxy]: https://galaxy.ansible.com/delinea/ss
[galaxy]: https://galaxy.ansible.com/
[readme.md]: README.md
