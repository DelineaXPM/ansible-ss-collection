========================
Delinea.Platform_SecretServer Release Notes
========================

.. contents:: Topics

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
