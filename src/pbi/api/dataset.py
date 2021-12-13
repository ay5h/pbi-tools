import time
import json
import requests
from urllib.parse import urlparse
from pbi.tools import handle_request
from .datasource import Datasource


class Dataset:
    """An object representing a Power BI dataset. You can find the GUID by going to the setting page of the desired dataset and inspecting the URL:

        \https://app.powerbi.com/groups/7b0ce7b6-5055-45b2-a15b-ffeb34a85368/settings/datasets/**6b7b638b-8a67-4e7c-b9b9-f17601ae8e4a**

    :param workspace: :class:`~Workspace` object representing the PBI workspace that the dataset lives in
    :param dataset: a dictionary of attributes expected to include ``id``, ``name``, ``isEffectiveIdentityRequired``
    :return: :class:`~Dataset` object
    """

    def __init__(self, workspace, dataset):
        self.workspace = workspace
        self.id = dataset["id"]
        self.name = dataset["name"]
        self.has_rls = dataset["isEffectiveIdentityRequired"]

    def get_datasources(self):
        """Fetches a fresh list of data sources connected to this dataset.

        :return: array of :class:`~Datasource` objects
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/Default.GetBoundGatewayDatasources",
            headers=self.workspace.tenant.token.get_headers(),
        )
        handle_request(r)

        datasources = r.json()["value"]
        self.datasources = [Datasource(self, d) for d in datasources]
        return self.datasources

    def authenticate(self, credentials):
        """Use the provided credentials to reauthenticate datasources connected to this dataset. If any of the provided credentials do not match the data source they will be skipped.

        Currently, only server and web-based credentials are supported using either username and password or oauth tokens.

        :param credentials: a dictionary of credentials (see examples in :meth:`~Workspace.refresh_datasets`)
        """

        for datasource in self.get_datasources():
            connection = json.loads(datasource.connection_details)
            server = connection.get("server")
            url = connection.get("url")

            if server:  # Server-based connections (e.g. Azure Data Warehouse)
                if server in credentials:
                    print(f"*** Updating credentials for {server}")
                    cred = credentials.get(server)

                    if "token" in cred:
                        datasource.update_credentials(token=cred["token"])
                    elif "username" in cred:
                        datasource.update_credentials(
                            cred["username"], cred["password"]
                        )
                else:
                    print(
                        f"*** No credentials provided for {server}. Using existing credentials."
                    )

            elif url:  # Web-based connections (e.g. Application Insights API)
                domain = urlparse(
                    url
                ).netloc  # Extract (sub)domain from full url endpoint
                if domain in credentials:
                    print(f"*** Updating credentials for {domain}")
                    cred = credentials.get(domain)

                    if "token" in cred:
                        datasource.update_credentials(token=cred["token"])
                    elif "username" in cred:
                        datasource.update_credentials(
                            cred["username"], cred["password"]
                        )
                else:
                    print(
                        f"*** No credentials provided for {domain}. Using existing credentials."
                    )

            else:
                print(
                    f"*** No credentials provided for {connection}. Using existing credentials."
                )

    def trigger_refresh(self):
        """Trigger a refresh of this dataset. This is an async call and you will need to check the refresh status separately using :meth:`~get_refresh_state`

        :param credentials: a dictionary of credentials (see examples in :meth:`~Workspace.refresh_datasets`)
        """

        r = requests.post(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/refreshes",
            headers=self.workspace.tenant.token.get_headers(),
        )
        handle_request(r)

    def get_refresh_state(self, wait=False, retries=5):
        """Check the status of the latest refresh of this dataset. If there is no completed or in progress refresh, returns 'No refreshes'.

        :param wait: if there is a refresh in progress, whether to keep checking until it completed or return an 'Unknown' status first time (i.e. in progress)
        :param retries: if we ask Power BI about the state of a refresh too quickly, it will return empty; this states how many times to try again before giving up
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/refreshes?$top=1",
            headers=self.workspace.tenant.token.get_headers(),
        )
        handle_request(r)

        if len(r.json()["value"]) == 0:
            if wait and retries > 0:
                print(f"No refresh found, trying again. Retries remaining: {retries}")
                time.sleep(60)
                return self.get_refresh_state(wait, retries=retries - 1)
            else:
                return "No refresh found"
        else:
            refresh = r.json()["value"][0]
            if wait and refresh["status"] == "Unknown":  # still refreshing
                # print(f'Refreshing [{self.name}], waiting 60 seconds...')
                time.sleep(60)
                return self.get_refresh_state(wait)
            elif refresh["status"] == "Failed":
                return refresh["serviceExceptionJson"]
            else:
                return refresh["status"]

    def get_params(self):
        """Returns the model parameters in a list.

        :return: array of dictionaries - parameter name sits in ``name`` key
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/parameters",
            headers=self.workspace.tenant.token.get_headers(),
        )
        json = handle_request(r)
        return json.get("value")

    def update_params(self, params):
        """Updates the model parameters using the provided values. The parameter keys provded must be an exact and complete match to those in the model.

        :return: array of dictionaries (see example below)

        .. code-block:: python

            >>> param1 = {'name': 'param1', 'newValue': 'value1'}
            >>> param2 = {'name': 'param2', 'newValue': 'value2'}
            >>> dataset.update_params({'updateDetails': [param1, param2]]}
        """

        r = requests.post(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/Default.UpdateParameters",
            headers=self.workspace.tenant.token.get_headers(),
            json=params,
        )
        handle_request(r)

    def take_ownership(self):
        """Take ownership of the model (using the identity used to authenticate with the :class:`~Workspace` object).

        If the user does not have ownership of the model, some other actions will fail (e.g. :meth:`~update_params`, :meth:`~authenticate`)
        """

        r = requests.post(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/Default.TakeOver",
            headers=self.workspace.tenant.token.get_headers(),
        )
        handle_request(r)

    def delete(self):
        """Delete this model from the workspace."""

        r = requests.delete(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}",
            headers=self.workspace.tenant.token.get_headers(),
        )
        handle_request(
            r, allowed_codes=[404]
        )  # Don't fail it dataset has already been deleted
