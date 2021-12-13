import os
import time
import requests
from os import path

from .report import Report
from .dataset import Dataset
from pbi.tools import handle_request, rebind_report

def _name_builder(filepath, **kwargs):
    filename = path.basename(filepath)
    return path.splitext(filename)[0]  # Get file stem (i.e. no extension)


def _name_comparator(a, b, **kwargs):
    return a == b


class Workspace:
    """An object representing a Power BI workspace. You can find the GUID by going to the workspace and inspecting the URL:

        \https://app.powerbi.com/groups/**7b0ce7b6-5055-45b2-a15b-ffeb34a85368**/list/dashboards

    :param id: the Power BI workspace GUID
    :param tenant_id: the Azure tenant GUID in which the Power BI workspace lives
    :param principal: service principal GUID
    :param secret: associated secret value to authenticate the service principal
    :return: :class:`~Workspace` object
    """

    def __init__(self, tenant, id):
        self.id = id
        self.tenant = tenant

        self._get_name()
        self.get_datasets()
        self.get_reports()

    def _get_name(self):
        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups?$filter=contains(id,'{self.id}')",
            headers=self.tenant.token.get_headers(),
        )
        json = handle_request(r)

        self.name = json.get("value")[0]["name"]
        return self.name

    def get_users_access(self):
        """Fetches a fresh list of users with access to this workspace.
        Includes both human and service principals.

        :return: array of dictonaries, each representing a user
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.id}/users",
            headers=self.tenant.token.get_headers(),
        )
        json = handle_request(r)

        self.users = json.get("value")
        return self.users

    def grant_user_access(self, user_access):
        """Grant access to this workspace to the given user.
        Will intelligently handle both create and update scenarios.
        """

        identifiers = [
            u.get("identifier") for u in self.get_users_access()
        ]  # list of emails/principal GUIDs
        method = (
            "put" if user_access.get("identifier") in identifiers else "post"
        )  # put/post based on whether user already exists
        r = requests.request(
            method,
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.id}/users",
            headers=self.tenant.token.get_headers(),
            json=user_access,
        )
        handle_request(r)

    def copy_permissions(self, reference_workspace):
        """Copying the access setup from another workspace.

        :param reference_workspace: the workspace GUID of another workspace to copy access setup from
        """

        for user in reference_workspace.get_users_access():
            self.grant_user_access(user)

    def get_datasets(self):
        """Fetches a fresh list of datasets from the PBI service.

        :return: array of :class:`~Dataset` objects
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.id}/datasets",
            headers=self.tenant.token.get_headers(),
        )
        json = handle_request(r)

        self.datasets = [Dataset(self, d) for d in json.get("value")]
        return self.datasets

    def get_dataset(self, dataset_id):
        """Fetches the dataset with the given GUID. You can find the GUID by going to the setting page of the desired dataset and inspecting the URL:

            \https://app.powerbi.com/groups/7b0ce7b6-5055-45b2-a15b-ffeb34a85368/settings/datasets/**6b7b638b-8a67-4e7c-b9b9-f17601ae8e4a**

        :param dataset_id: the dataset GUID
        :return: a :class:`~Dataset` object
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.id}/datasets/{dataset_id}",
            headers=self.tenant.token.get_headers(),
        )
        json = handle_request(r)

        return Dataset(self, json)

    def find_dataset(self, dataset_name):
        """Tries to fetch the dataset with the given name.
        If more than one dataset is found, only the first is returned.
        The order is defined by Power BI.

        :param report_name: the dataset name
        :return: a :class:`~Dataset` object (or ``None``)
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.id}/datasets",
            headers=self.tenant.token.get_headers(),
        )
        json = handle_request(r)

        for r in json.get("value"):
            if r.get("name") == dataset_name:
                return Dataset(self, r)

    def get_reports(self):
        """Fetches a fresh list of reports from the PBI service.

        :return: array of :class:`~Report` objects
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.id}/reports",
            headers=self.tenant.token.get_headers(),
        )
        handle_request(r)

        reports = r.json()["value"]
        self.reports = [Report(self, r) for r in reports]
        return self.reports

    def get_report(self, report_id):
        """Fetches the report with the given GUID. You can find the GUID by going to the report and inspecting the URL:

            \https://app.powerbi.com/groups/7b0ce7b6-5055-45b2-a15b-ffeb34a85368/reports/**4702db31-bc75-422c-92b4-b6a0809b0f1a**/ReportSection

        :param report_id: the report GUID
        :return: a :class:`~Report` object
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.id}/reports/{report_id}",
            headers=self.tenant.token.get_headers(),
        )
        json = handle_request(r)

        return Report(self, json)

    def find_report(self, report_name):
        """Tries to fetch the report with the given name.
        If more than one report is found, only the first is returned.
        The order is defined by Power BI.

        :param report_name: the report name
        :return: a :class:`~Report` object (or ``None``)
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.id}/reports",
            headers=self.tenant.token.get_headers(),
        )
        json = handle_request(r)

        for r in json.get("value"):
            if r.get("name") == report_name:
                return Report(self, r)

    def publish_file(self, filepath, name, skipReports=False, overwrite_reports=False):
        """Publishes the given PBIX file to the workspace.
        If a model/report already exists with the same name, the new model/report is published alongside it.

        :param filepath: absolute *or* relative path to the PBIX file which is to be published
        :param name: desired name for the model/report
        :param skipReports: whether to supress the publishing of reports (i.e. publish only the model)
        :return: a tuple of arrays - first of :class:`~Dataset` objects, second of :class:`~Report` objects
        """

        nameConflict = "CreateOrOverwrite" if overwrite_reports else "Ignore"
        params = {"datasetDisplayName": name + ".pbix", "nameConflict": nameConflict}
        if skipReports:
            params["skipReport"] = "true"

        payload = {}
        with open(filepath, "rb") as f:
            payload["file"] = open(filepath, "rb")

        r = requests.post(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.id}/imports",
            params=params,
            headers=self.tenant.token.get_headers(),
            files=payload,
        )
        json = handle_request(r)
        import_id = json.get("id")

        # Check whether import has finished, wait and retry if not
        while True:
            r = requests.get(
                f"https://api.powerbi.com/v1.0/myorg/groups/{self.id}/imports/{import_id}",
                headers=self.tenant.token.get_headers(),
            )
            json = handle_request(r)
            import_status = json.get("importState")

            if import_status == "Succeeded":
                datasets = [self.get_dataset(d.get("id")) for d in json.get("datasets")]
                reports = [self.get_report(r.get("id")) for r in json.get("reports")]

                return datasets, reports

            elif import_status == "Publishing":
                time.sleep(10)
                continue

            else:
                print(
                    f'Import ERROR: {json.get("error").get("code")} ({json.get("error").get("message")})'
                )
                break

    def refresh_datasets(self, credentials=None, wait=True):
        """Refreshes all datasets in the workspace, optionally reauthenticating using the credentials provided. Currently, only database credentials are supported using either SQL logins or oauth tokens.

        :param credentials: a dictionary of credentials (see examples below)
        :param wait: whether to wait for all models to finish refreshing before returning
        :return: a `Boolean` indicating whether all models refreshed successfully (if waiting)

        .. code-block:: python

            >>> creds = {}
            >>> creds['serverA.database.windows.net'] = {'username': 'db_username', 'password': 'db_password'}
            >>> creds['serverB.database.windows.net'] = {'token': 'oauth_token'}

            >>> pbi_token = Token(f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token', 'https://analysis.windows.net/powerbi/api/.default', pbi_sp, pbi_sp_secret)
            >>> workspace = Workspace(workspace_id, pbi_token)
            >>> result = workspace.refresh_datasets(creds)

            >>> result
            True
        """

        error = False
        datasets = [d for d in self.datasets if "Deployment Aid" not in d.name]

        for dataset in datasets:
            try:
                if (
                    dataset.get_refresh_state() == "Unknown"
                ):  # Don't trigger refresh if model is already refreshing
                    print(f"** [{dataset.name}] is already refreshing")
                else:
                    print(f"** Reconfiguring [{dataset.name}]")
                    dataset.take_ownership()  # In case someone manually took control post deployment

                    if credentials:
                        print(
                            f"*** Reauthenticating data sources..."
                        )  # Reauthenticate as tokens obtained during deployment will have expired
                        dataset.authenticate(credentials)

                    print(
                        f"*** Starting refresh..."
                    )  # We check back later for completion
                    dataset.trigger_refresh()

            except SystemExit as e:
                print(f"!! ERROR. Triggering refresh failed for [{dataset.name}]. {e}")
                error = True

        if wait:
            print("* Waiting for models to finish refreshing...")
            for dataset in datasets:
                try:
                    refresh_status = dataset.get_refresh_state(
                        wait=True
                    )  # Wait for each refresh to complete
                    if refresh_status == "Completed":
                        print(f"** Refresh complete for [{dataset.name}]")
                    else:
                        raise SystemExit(refresh_status)

                except SystemExit as e:
                    print(f"!! ERROR. Refresh failed for [{dataset.name}]. {e}")
                    error = True

            return not error

    def deploy(
        self,
        dataset_filepath,
        report_filepaths,
        dataset_params=None,
        credentials=None,
        force_refresh=False,
        on_report_success=None,
        name_builder=_name_builder,
        name_comparator=_name_comparator,
        overwrite_reports=False,
        **kwargs,
    ):
        """Publishes a single model and an collection of associated reports. Note, currently only database authentication is supported, using either SQL logins or oauth tokens.

        There is a requirement for a dummy report called 'Deployment Aid Report' to exist either in the publishing workspace (default) or in a separate 'config' workspace.

        You can optionally provide a function to define the model/report names and a function to execute any 'wrap up' steps after a successful report publish. You can pass through additional data that might be useful to these functions using the ``**kwargs``.

        :param dataset_filepath: path to the model PBIX file
        :param report_filepaths: an array of paths to report PBIX files
        :param dataset_params: a dictionary of parameters to be applied to the model
        :param credentials: a dictionary of credentials (see examples in :meth:`~refresh_datasets`)
        :param force_refresh: force the model to refresh even if does not meet other criteria
        :param on_report_success: a function that is called after each report is successfully published - passing the report object and ``**kwargs``
        :param name_builder: a function that returns the desired model/report name - passing the report object and ``**kwargs``
        :param config_workspace: a separate workspace in which to look for the 'Deployment Aid Report'
        :param kwargs: options passed through to ``on_report_success()`` and ``name_builder()`` functions

        .. code-block:: python

            >>> report_paths = ['path/to/reportA', 'path/to/reportB']
            >>> params = {'schema': 'db_schema'}

            >>> creds = {}
            >>> creds['serverA.database.windows.net'] = {'username': 'db_username', 'password': 'db_password'}

            >>> pbi_token = Token(f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token', 'https://analysis.windows.net/powerbi/api/.default', pbi_sp, pbi_sp_secret)
            >>> workspace = Workspace(workspace_id, pbi_token)
            >>> result = workspace.deploy('path/to/model', report_paths, params, creds)

            >>> result
            True

        An example of a ``name_builder()`` function that prefixes the filename with a 'group' value passed through from the calling function:

        .. code-block:: python

            def name_builder(filepath, **kwargs):
                components = [kwargs.get('group'), os.path.basename(filepath)]
                return ' -- '.join(components)

        An example of an ``on_report_success()`` function that prints to the console each time a report is successfully published:

        .. code-block:: python

            def on_report_success(report, **kwargs):
                print(f'Report deployed! {report.name}')
        """

        # 1. Get dummy connections string from 'aid report' in config workspace
        aid_model, aid_report = self.tenant.get_deployment_aids()
        connection_string = self.tenant.get_aid_connection_string()

        # 2. Publish dataset or get existing dataset (if unchanged and current)
        dataset_name = name_builder(dataset_filepath, **kwargs)
        matching_datasets = [
            d
            for d in self.datasets
            if name_comparator(d.name, dataset_name, overwrite_reports=overwrite_reports)
        ]  # Look for existing dataset

        if (
            not matching_datasets or force_refresh
        ):  # Only publish dataset if there isn't one already, or it's marked as needing a refresh
            print(f"** Publishing dataset [{dataset_filepath}] as [{dataset_name}]...")
            new_datasets, new_reports = self.publish_file(
                dataset_filepath,
                dataset_name,
                skipReports=True,
                overwrite_reports=overwrite_reports,
            )
            dataset = new_datasets.pop()
        else:
            dataset = (
                matching_datasets.pop()
            )  # Get the latest dataset (and remove from list of matches, which is deleted later)
            print(f"** Using existing dataset [{dataset.name}]")

        # 3. Update params and credentials, then refresh (unless current)
        refresh_state = dataset.get_refresh_state()
        if refresh_state == "Completed" and not overwrite_reports:
            print("** Existing dataset valid")
        else:
            if (
                refresh_state != "Unknown"
            ):  # Unknown == refreshing; therefore either last refresh failed, or there has never been a refresh attempt
                dataset.take_ownership()  # Publishing does not change ownership, so make sure we own it before continuing

                if dataset_params:
                    print("*** Updating parameters...")
                    param_keys = [p["name"] for p in dataset.get_params()]
                    params = [
                        {"name": k, "newValue": v}
                        for k, v in dataset_params.items()
                        if k in param_keys
                    ]  # Only try to update params that are defined for this dataset
                    if params:
                        dataset.update_params({"updateDetails": params})

                if credentials:
                    print("*** Authenticating...")
                    dataset.authenticate(credentials)

                print("*** Triggering refresh")  # We check back later for completion
                dataset.trigger_refresh()

            # 4. Wait for refresh to complete (stop on error)
            refresh_state = dataset.get_refresh_state(
                wait=True
            )  # Wait for any dataset refreshes to finish before continuing
            if refresh_state == "Completed":
                print(
                    "*** Dataset refreshed"
                )  # Don't report completed refresh if we used an existing dataset
            else:
                raise SystemExit(f"Refresh failed: {refresh_state}")

        # 5. Publish reports (using dummy connection string initially)
        for filepath in report_filepaths:  # Import report files
            report_name = name_builder(filepath, **kwargs)
            matching_reports = [
                r
                for r in self.reports
                if name_comparator(r.name, report_name, overwrite_reports=overwrite_reports)
            ]  # Look for existing reports
            if overwrite_reports:
                for report in matching_reports:
                    report.repoint(aid_model)

            print(
                f"** Publishing report [{filepath}] as [{report_name}]..."
            )  # Alter PBIX file with dummy dataset, in case dataset used during development has since been deleted (we repoint once on service)
            rebind_report(filepath, connection_string)
            new_datasets, new_reports = self.publish_file(
                filepath, report_name, overwrite_reports=overwrite_reports
            )

            # 6. Repoint to refreshed model and update Portals (if given)
            for report in new_reports:
                report.repoint(
                    dataset
                )  # Once published, repoint from dummy to new dataset
                if on_report_success:
                    try:
                        on_report_success(
                            report, **kwargs
                        )  # Perform any final post-deploy actions
                    except Exception as e:
                        print(f"! WARNING. Error executing post-deploy steps. {e}")

            # 7. Delete old reports
            if not overwrite_reports:
                for old_report in matching_reports:
                    print(f"*** Deleting old report [{old_report.name}]")
                    old_report.delete()

        # 8. Delete old models
        if not overwrite_reports:
            for old_dataset in matching_datasets:
                print(f"** Deleting old dataset [{old_dataset.name}]")
                old_dataset.delete()
