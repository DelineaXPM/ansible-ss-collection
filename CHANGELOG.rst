========================
Delinea.Platform_SecretServer Release Notes
========================

.. contents:: Topics

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
