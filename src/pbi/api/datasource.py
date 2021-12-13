import json
import requests
from pbi.tools import handle_request


class Datasource:
    """An object representing a Power BI datasource. You can find the GUID by going to the lineage view and clicking 'show impact' button on the data source, then inspecting the URL:

        \https://app.powerbi.com/groups/7b0ce7b6-5055-45b2-a15b-ffeb34a85368/lineage?datasourceId=**ecc6affe-5bbd-4504-a3e7-14d4aae902d8**&src=datasourceCredentials&actions=impact

    :param dataset: :class:`~Dataset` object representing a PBI dataset that the report is attatched to
    :param datasource: a dictionary of attributes expected to include ``id``, ``gateway_id`` and ``connection_details``
    :return: :class:`~Datasource` object
    """

    def __init__(self, dataset, datasource):
        self.dataset = dataset
        self.id = datasource["id"]
        self.gateway_id = datasource["gatewayId"]
        self.connection_details = datasource["connectionDetails"]

    def update_credentials(self, username=None, password=None, token=None):
        """Use the provided credentials to reauthenticate datasources connected to this dataset. If any of the provided credentials do not match the data source they will be skipped.

        Currently, only database credentials are supported using either SQL logins or oauth tokens.

        Warning: If you use the oauth method, then authentiaction will only remain valid until the token expires - you may need to reauthenticate before refreshing; the token may expire before the refresh has completed in large models.

        :param username: username value if using SQL authentication; the ``password`` must also be provided
        :param password: password value if using SQL authentication; the ``username`` must also be provided
        :param token: valid oauth token (an alternative to passing username and password)
        """

        if token:
            auth = "OAuth2"
            credentials = {
                "credentialData": [{"name": "accessToken", "value": token.get_token()}]
            }
        else:
            auth = "Basic"
            credentials = {
                "credentialData": [
                    {"name": "username", "value": username},
                    {"name": "password", "value": password},
                ]
            }

        payload = {
            "credentialDetails": {
                "credentialType": auth,
                "credentials": json.dumps(credentials),
                "encryptedConnection": "Encrypted",
                "encryptionAlgorithm": "None",
                "privacyLevel": "Organizational",
                "useCallerAADIdentity": "False",  # required to avoid direct query connections 'expiring'
                "useEndUserOAuth2Credentials": "False",  # required to avoid direct query connections 'expiring'
            }
        }

        r = requests.patch(
            f"https://api.powerbi.com/v1.0/myorg/gateways/{self.gateway_id}/datasources/{self.id}",
            headers=self.dataset.workspace.tenant.token.get_headers(),
            json=payload,
        )
        handle_request(r)
