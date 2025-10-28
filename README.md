# Ansible Collection - delinea.ss

![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/delineaxpm/ansible-ss-collection?style=for-the-badge)

Ansible core collection for Delinea Secret Server.

## Included content

### Lookup plugins

| Name                            | Description                                        |
| ------------------------------- | -------------------------------------------------- |
| [delinea.ss.tss](docs/tss.md) | Look up secrets from Delinea Secret Server. |

## External requirements

This collection requires the `python-tss-sdk` library to interact with Delinea Secret Server. You must install this Python package in your environment:

```shell
pip install python-tss-sdk
```

To use platform authentication, `python-tss-sdk` must be version 2.0.1 or higher.
Refer to the [python-tss-sdk documentation](https://pypi.org/project/python-tss-sdk/) for more details and advanced usage.

## Using this collection

### Installing the Collection from Ansible Galaxy

Before using this collection, you need to install it with the Ansible Galaxy command-line tool:

```shell
ansible-galaxy collection install delinea.ss
```

You can also include it in a `requirements.yml` file and install it with
`ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: delinea.ss
```

Note that if you install the collection from Ansible Galaxy, it will not be upgraded
automatically when you upgrade the `ansible` package. To upgrade the collection to
the latest available version, run the following command:

```shell
ansible-galaxy collection install delinea.ss --upgrade
```

You can also install a specific version of the collection, for example, if you need
to downgrade when something is broken in the latest version (please report an issue
in this repository). Use the following syntax to install version `1.0.0`:

```shell
ansible-galaxy collection install delinea.ss:==1.0.0
```

See [Ansible Using collections](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html) for more details.

## Contributing

Read the [Development Guide](DEVELOPER.md) to learn about our build, test, and release processes.
