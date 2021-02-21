PBI Tools
=========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

**PBI Tools** is an object-orientated Python library that makes working with Power BI files easier. It was designed to enable automated deployment in a DevOps environment.

Installation
============

To install, simply: ::

   $ python -m pip install pbi-tools

Getting Started
===============

The simplest use case:

.. code-block:: python

   pbi_token = Token(f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token', 'https://analysis.windows.net/powerbi/api/.default', 'SP', 'SECRET')
   workspace = Workspace(workspace_id, pbi_token)
   print(f'* This is the [{workspace.name}] workspace')

API Reference
=============

Full documentation of all functions.

.. module:: pbi

Workspace
---------
.. autoclass:: Workspace
   :members:

Report
------
.. autoclass:: Report
   :members:

Dataset
-------
.. autoclass:: Dataset
   :members:

Datasource
----------
.. autoclass:: Datasource
   :members:

Token
-----
.. autoclass:: Token
   :members: