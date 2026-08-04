============================================
Delinea.Platform\_SecretServer Release Notes
============================================

.. contents:: Topics

v1.3.0
======

Release Summary
---------------

Reconcile the ``tss`` lookup with the ``community.general`` ``tss`` lookup interface: reject the unsupported ``_terms`` keyword argument, type ``_terms`` as a list of integer secret IDs, and document the intentional empty ``token_path_uri`` default that lets ``python-tss-sdk`` auto-detect Secret Server versus the Delinea Platform token endpoint, and add a ``token_path_source`` option to control how that endpoint is resolved.

Minor Changes
-------------

- tss lookup plugin - add the ``token_path_source`` option (``token_path_uri`` or ``auto``) to control how the OAuth2 token endpoint is resolved; ``auto`` forces ``python-tss-sdk`` endpoint auto-detection regardless of ``token_path_uri`` (reconciles with the ``community.general`` ``tss`` lookup).
- tss lookup plugin - document that OAuth2 token endpoint auto-detection - an empty ``token_path_uri`` (the default) or ``token_path_source=auto`` - requires ``python-tss-sdk`` 2.0.1 or greater.
- tss lookup plugin - document that an empty ``token_path_uri`` (the default) lets the SDK auto-detect Secret Server versus the Delinea Platform and select the correct token endpoint.
- tss lookup plugin - reject the unsupported ``_terms`` keyword argument and guide users to pass secret IDs as positional arguments (reconciles with the ``community.general`` ``tss`` lookup).
- tss lookup plugin - the ``_terms`` argument is now typed as a list of integer secret IDs (``type: list`` / ``elements: int``) to match how Ansible passes lookup terms.
- tss lookup plugin - the ``token_path_uri`` and ``token_path_source`` options can now be set in ``ansible.cfg`` under the ``[tss_lookup]`` section, matching the other connection options and the ``community.general`` ``tss`` lookup.

v1.2.0
======

Release Summary
---------------

Cache the ``TSSClient`` per Ansible process and credential identity so OAuth2
token grants are reused across ``tss`` lookups, reducing load on the
``/oauth2/token`` endpoint and avoiding intermittent token-endpoint failures
under playbooks with many lookups. Adds a one-time retry that rebuilds the
cached client on a stale-token 4xx. Also fixes the ``tss`` lookup EXAMPLES
that subscripted a JSON-string result without ``| from_json``.

Minor Changes
-------------

- tss lookup plugin - cache the ``TSSClient`` per Ansible process and credential identity so OAuth2 token grants are reused across lookups. Previously every ``lookup()`` invocation built a fresh client and minted a new ``/oauth2/token`` grant; under playbooks with many lookups this could trigger intermittent token endpoint failures.
- tss lookup plugin - on a 4xx response from Secret Server (e.g. an expired cached token), invalidate the cached ``TSSClient`` for that credential identity, rebuild it, and retry the lookup once. 5xx responses propagate unchanged. This covers the edge-of-expiry window the SDK does not refresh through.

Bugfixes
--------

- tss lookup plugin docs - the EXAMPLES for username/password and Platform-service-user lookups (no attachments, no secret_path) were subscripting the lookup result as if it were a dict, but the plugin returns a JSON string on that code path. Added ``| from_json`` to the four affected examples in ``plugins/lookup/tss.py`` and the matching blocks in ``docs/tss.md`` so they run as written. No plugin behavior change.

v1.1.0
======

Release Summary
---------------

Added optional comment parameter to tss lookup plugin for audit trail logging.
When retrieving secrets, users can now provide a comment that will be logged
in Secret Server's audit trail. This is particularly useful when the
"Require Comment" option is enabled under the Security tab of a secret.

v1.0.0
======

Release Summary
---------------

New plugin for getting secrets from Delinea Secret Server in Ansible.
Enhanced AccessTokenAuthorizer to support both Secret Server and Platform authentication.
The token-based authentication now automatically detects the server type based on the
base_url parameter, enabling seamless integration with both Secret Server instances
and Delinea Platform services.

New Plugins
-----------

Lookup
~~~~~~

- delinea.platform_secretserver.tss - Get secrets from Delinea Secret Server
