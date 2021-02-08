import time
import requests
from .tools import handle_request
        
class Dataset:
    def __init__(self, workspace, dataset):
        self.workspace = workspace
        self.id = dataset['id']
        self.name = dataset['name']
        self.has_rls = dataset['isEffectiveIdentityRequired']

    def get_datasources(self):
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/Default.GetBoundGatewayDatasources', headers=self.workspace.get_headers())
        handle_request(r)

        datasources = r.json()['value']
        self.datasources = [Datasource(self, d) for d in datasources]
        return self.datasources
 
    def trigger_refresh(self):
        r = requests.post(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/refreshes', headers=self.workspace.get_headers())
        handle_request(r)

    def get_refresh_state(self, wait=False):
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/refreshes?$top=1', headers=self.workspace.get_headers())
        handle_request(r)
        
        if len(r.json()['value']) == 0:
            return 'No refreshes'
        else:
            refresh = r.json()['value'][0]
            if wait and refresh['status'] == 'Unknown': # still refreshing
                #print(f'Refreshing [{self.name}], waiting 60 seconds...')
                time.sleep(60)
                return self.get_refresh_state(wait)
            elif refresh['status'] == 'Failed':
                return refresh['serviceExceptionJson']
            else:
                return refresh['status']

    def get_params(self):
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/parameters', headers=self.workspace.get_headers())
        json = handle_request(r)
        return json.get('value')
    
    def update_params(self, params):
        r = requests.post(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/Default.UpdateParameters', headers=self.workspace.get_headers(), json=params)
        handle_request(r)

    def take_ownership(self):
        r = requests.post(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}/Default.TakeOver', headers=self.workspace.get_headers())
        handle_request(r)

    def delete(self):
        r = requests.delete(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/datasets/{self.id}', headers=self.workspace.get_headers())
        handle_request(r)