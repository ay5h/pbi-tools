import requests

from .token import Token
from .workspace import Workspace
from .tools import handle_request

class Tenant:
    """An object representing an Azure tenant.
    
    :param id: the Azure tenant GUID
    :param principal: service principal GUID
    :param secret: associated secret value to authenticate the service principal
    :return: :class:`~Tenant` object
    """

    def __init__(self, id, sp, secret):
        pbi_oauth_url = f'https://login.microsoftonline.com/{id}/oauth2/v2.0/token'
        scope = 'https://analysis.windows.net/powerbi/api/.default'
        self.token = Token(pbi_oauth_url, scope, sp, secret)

    def _get_headers(self):
        return {'Authorization': f'Bearer {self.token.get_token()}'}

    def get_workspaces(self):
        """Fetch a list of all workspaces that the user has access to.
    
        :return: Array of :class:`~Workspace` objects
        """

        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups', headers=self._get_headers())
        json = handle_request(r)

        self.workspaces = [Workspace(self, w.get('id')) for w in json.get('value')]
        return self.workspaces

    def find_workspace(self, workspace_name):
        """Tries to fetch the workspace with the given name.

        :param workspace__name: the workspace GUID
        :return: a :class:`~Workspace` object (or ``None``)
        """

        workspaces = self.get_workspaces()
        for workspace in workspaces:
            if workspace.get('name') == workspace_name:
                return Workspace([self, workspace.get('id')])

    def create_workspace(self, name, reference_workspace=None):
        """Creates a new workspace, optionally copying the access setup from another workspace.

        :param reference_workspace: the workspace GUID of another workspace to copy access setup from
        :return: a :class:`~Workspace` object
        """

        payload = {"name": name}
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups', headers=self._get_headers(), json=payload)
        json = handle_request(r)
        workspace = Workspace([self, json.get('id')])

        # If a reference workspace is given, replicate users' access settings
        if reference_workspace:
            for user in workspace.get_users_access():
                workspace.grant_user_access(user)

        return workspace