========================
Delinea.SS Release Notes
========================

.. contents:: Topics

v1.2.0
======

Release Summary
---------------

Enhanced AccessTokenAuthorizer to support both Secret Server and Platform authentication.
The token-based authentication now automatically detects the server type based on the 
base_url parameter, enabling seamless integration with both Secret Server instances 
and Delinea Platform services.

v1.1.0
======

Release Summary
---------------

Updated plugin description and added changelogs.

v1.0.0
======

Release Summary
---------------

New plugin for getting secrets from Delinea Secret Server in Ansible.

New Plugins
-----------

Lookup
~~~~~~

- delinea.ss.tss - Get secrets from Delinea Secret Server
