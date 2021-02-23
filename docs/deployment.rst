Deployment
==========

PBI Tools was built to simplify CICD for Power BI.
The examples on this page grow in complexity, each demonstrating a specific piece of functionality.

For all examples, consider the following simple project repository. ``deploy.py`` is responsible for deploying the files in the ``pbi`` directory.

.. code-block::

  project
    ├── deploy.py
    └── pbi          
        ├── Model.pbix
        ├── Report A.pbix
        ├── Report B.pbix
        └── Report C.pbix

Base Case
---------

The example below provides the simplest use case - deploy a model and set of associated reports:

.. code-block:: python

    from pbi import Workspace

    # 1. Connect to workspace
    workspace = Workspace('workspace_guid', 'tenant_guid', 'service_principal', 'secret')
    print(f'Connected to {workspace.name} workspace!')

    # 2. Look for the model file
    dataset_file = 'Model.pbix'
    if not os.path.exists(dataset_file):
        print(f'! Warning: No model found in [{dir}]. Skipping folder.')
        contin
        
    # 3. Find report files, including in subfolders (but ignoring model)
        report_files = []
        for sub_root, sub_dirs, sub_files in os.walk(os.path.join(root, dir)):
            new_reports = [os.path.join(sub_root, f) for f in sub_files if os.path.splitext(f)[1] == '.pbix' and f != 'Model.pbix']
            report_files.extend(new_reports)

    # 4. Deploy
    print(f'* Deploying {len(report_files)} reports')
    workspace.deploy(dataset_file, report_files)

Model Parameters
----------------

To come.

Data Source Credentials
-----------------------

To come.

Custom Report Names
-------------------

To come.

Post Deploy Actions
-------------------

To come.