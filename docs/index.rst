PBI Tools
=========

**PBI Tools** is an object-orientated Python library that makes working with Power BI files easier.

It was designed to support Power BI development and deployment (CICD).
Specifically, it looks to solve two common problems:

1. Storing PBIX files in repos without also storing the data
2. Publishing reports that point to a separate Power BI model that no longer exists (e.g. the model used during development has since been superceded).

.. warning::
   This library is currently in alpha - feel free to use it experimentally.
   If you do come across any issues, feel free to raise them on the `GitHub page <https://github.com/thomas-daughters/pbi-tools/issues>`_.

Installation
------------

.. code-block::

   $ pip install pbi-tools

Getting Started
---------------

First, create a workspace object:

.. code-block:: python

   from pbi import Workspace

   workspace = Workspace(workspace_id, tenant_id, service_principal, secret)
   print(f'Connected to the {workspace.name} workspace!')

We can do some useful things just using the workspace, for example refresh all datasets:

.. code-block:: python

   workspace.refresh(wait=True)

Rename all reports in just a few lines:

.. code-block:: python

   reports = workspace.get_reports()
   for report in reports:
      new_name = f'{report.name} - Archived'
      report.rename(new_name)

Or get the parameters for a given model:

.. code-block:: python

   import pprint as pp

   dataset = workspace.find_dataset('My Dataset')
   params = dataset.get_parameters()
   pp.pprint(params)

Deployment Guide
----------------

This section walks through a typical deployment setup.

.. toctree::
   deployment
   prerequisites

API Reference
-------------

Full documentation for all public classes and methods.

.. toctree::
   api/tenant
   api/workspace
   api/report
   api/dataset
   api/datasource
   api/token

There are a few standalone functions that are used by the class methods, but may also be useful on their own.

.. toctree::
   api/tools

Authors
-------

PBI Tools was written by **Sam Thomas** while working at Redkite Data Intelligence Ltd.
Other contributors are:

* Andy Shao
* Peter Sach