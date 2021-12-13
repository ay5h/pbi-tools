import os
import requests

from .workspace import Workspace
from pbi.token import Token
from pbi.tools import handle_request, get_connection_string

DEPLOYMENT_AID_NAME = "Deployment Aid"

class Tenant:
    """An object representing an Azure tenant.

    :param id: the Azure tenant GUID
    :param principal: service principal GUID
    :param secret: associated secret value to authenticate the service principal
    :return: :class:`~Tenant` object
    """

    def __init__(self, id, sp, secret):
        pbi_oauth_url = f"https://login.microsoftonline.com/{id}/oauth2/v2.0/token"
        scope = "https://analysis.windows.net/powerbi/api/.default"
        self.token = Token(pbi_oauth_url, scope, sp, secret)
        
        self.get_workspaces()

    def _get_headers(self):
        return {"Authorization": f"Bearer {self.token.get_token()}"}

    def set_config_workspace(self, workspace_id):
        """Defines a workspace to be used for configuration, including deployment aids. Required before running deployment methods.
        
        :param workspace_id: GUID of workspace that contains the deployment aids
        """

        self.config_workspace = Workspace(self, workspace_id)

    def get_deployment_aids(self):
        """Looks for a deployment aid in the config workspace, returning it if found. Errors if config workspace or report not found.
        
        :return: (:class:`~Report`, :class:`~Report`) tuple
        """

        if not self.config_workspace:
            raise SystemExit("ERROR: Config workspace not set. Missing tenant.set_config_workspace()?")

        aid_model = self.config_workspace.find_dataset(DEPLOYMENT_AID_NAME)
        aid_report = self.config_workspace.find_report(DEPLOYMENT_AID_NAME)
        
        if not aid_model or not aid_report:
            raise SystemExit(f"ERROR: Deployment Aids not found. Looking for model and report called: {DEPLOYMENT_AID_NAME}")

        return aid_model, aid_report

    def get_aid_connection_string(self):
        """Downloads the aid report and extracts the data source connection string from the PBIX file.
        
        :return: Power BI dataset connection string
        """

        aid_model, aid_report = self.get_deployment_aids()

        with open(DEPLOYMENT_AID_NAME, "wb") as report_file:  # Get connection string from aid report
            report_file.write(aid_report.download())
        
        connection_string = get_connection_string(DEPLOYMENT_AID_NAME)

        os.remove(DEPLOYMENT_AID_NAME) # Remove temp aid report

        return connection_string

    def get_workspaces(self):
        """Fetch a list of all workspaces that the user has access to.

        :return: Array of :class:`~Workspace` objects
        """

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups", headers=self._get_headers()
        )
        json = handle_request(r)

        self.workspaces = [Workspace(self, w.get("id")) for w in json.get("value")]
        return self.workspaces

    def find_workspace(self, workspace_name):
        """Tries to fetch the workspace with the given name.

        :param workspace__name: the workspace GUID
        :return: a :class:`~Workspace` object (or ``None``)
        """

        workspaces = self.get_workspaces()
        for workspace in workspaces:
            if workspace.name == workspace_name:
                return Workspace(self, workspace.id)

    def create_workspace(self, name):
        """Creates a new workspace.

        :param name: the name of the new workspace
        :param reference_workspace: the workspace GUID of another workspace to copy access setup from
        :return: a :class:`~Workspace` object
        """

        payload = {"name": name}
        r = requests.post(
            f"https://api.powerbi.com/v1.0/myorg/groups",
            headers=self._get_headers(),
            json=payload,
        )
        json = handle_request(r)
        workspace = Workspace(self, json.get("id"))

        print(f"Created new workspace [{workspace.name}]")
        return workspace
