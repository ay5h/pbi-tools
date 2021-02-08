import json
import requests
from .tools import handle_request
        
class Datasource:
    def __init__(self, dataset, datasource):
        self.dataset = dataset
        self.id = datasource['id']
        self.gateway_id = datasource['gatewayId']
        self.connection_details = datasource["connectionDetails"]

    def update_credentials(self, username=None, password=None, token=None):
        if token:
            auth = 'OAuth2'
            credentials = {"credentialData": [{
                "name": "accessToken",
                "value": token.get_token()
            }]}
        else:
            auth = 'Basic'
            credentials = {"credentialData": [{
                "name": "username",
                "value": username
            }, {
                "name": "password",
                "value": password
            }]}

        payload = {'credentialDetails': {
            "credentialType": auth,
            "credentials": json.dumps(credentials),
            "encryptedConnection": "Encrypted",
            "encryptionAlgorithm": "None",
            "privacyLevel": "Organizational"
        }}
        r = requests.patch(f'https://api.powerbi.com/v1.0/myorg/gateways/{self.gateway_id}/datasources/{self.id}', headers=self.dataset.workspace.get_headers(), json=payload)
        handle_request(r)