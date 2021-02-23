Prerequisites
=============

Deployment Aid Report
---------------------

It is common practice to separate a PBI model into its own dedicated PBIX file, especially when the model is to be used by many reports.
However, this type of setup creates challenges at deployment time - what happens if the model that was used when a report was developed no longer exists?
Publishing will fail because Power BI will not be able to find the model referred to in the report PBIX file.

It is possible to modify the PBIX file programmatically, to point at another model.
However the required model identifier is not exposed by the REST API; the only way to obtain it is by copying it from another report.

To solve this problem in the general case, we suggest creating a pair of 'dummy' model and report files which never change.
These can be placed in each of your content workspaces, or in a separate 'configuration' workspace.
You can use any report pointing at any model, but the simplest case would be a model with some nominal pasted data, and an empty report.
The report must be named 'Deployment Aid Report'.

At deployment time, report files are modified before publishing to point to this dummy model.
Once deployed, they are repointed in the workspace to the correct model.

This approach may seem convoluted, but is required due to limitations in the REST API.

Dependencies
------------

PBI Tools uses the ubiquitous `Requests<https://requests.readthedocs.io>` package to interact with Power BI via its REST API.
There are no other code dependencies beyond the standard Python library.

Future breaking changes to the PBIX file format or the REST API endpoints may cause elements of PBI Tools to break or have undesired outcomes. The authors will endeavour to update this package before any such changes reach general release status.

Limitations
-----------

Not all Power BI REST endpoints are implemented by PBI Tools - only those required to achieve the project's objectives.