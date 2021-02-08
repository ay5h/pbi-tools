import time
from datetime import datetime, timedelta
import json
import requests
from .tools import handle_request
        
class Token:
    def __init__(self, url, scope, principal, secret):
        self.url = url
        self.scope = scope
        self.principal = principal
        self.secret = secret
        self.refresh()

    def refresh(self):
        payload = {
            'grant_type': 'client_credentials',
            'scope': self.scope,
            'client_id': self.principal,
            'client_secret': self.secret
        }
        r = requests.post(self.url, payload)
        handle_request(r)

        self.__token = r.json()['access_token']
        self.__token_expiry = datetime.now() + timedelta(minutes = 30)

    def get_token(self):
        if not self.__token or self.__token_expiry < datetime.now():
            self.refresh()
        return self.__token

class Workspace:
    def __init__(self, id, token):
        self.id = id
        self.token = token

        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups?$filter=contains(id,\'{self.id}\')', headers=self.get_headers())
        handle_request(r)
        self.name = r.json()['value'][0]['name']

        self.get_datasets()
    
    def get_headers(self):
        return {'Authorization': f'Bearer {self.token.get_token()}'}

    def get_datasets(self):
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.id}/datasets', headers=self.get_headers())
        json = handle_request(r)

        self.datasets = [Dataset(self, d) for d in json.get('value')]
        return self.datasets

    def get_dataset(self, dataset_id):
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.id}/datasets/{dataset_id}', headers=self.get_headers())
        json = handle_request(r)

        return Dataset(self, json)

    def get_reports(self):
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.id}/reports', headers=self.get_headers())
        handle_request(r)

        reports = r.json()['value']
        self.reports = [Report(self, r) for r in reports]
        return self.reports

    def get_report(self, report_id):
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.id}/reports/{report_id}', headers=self.get_headers())
        json = handle_request(r)

        return Report(self, json)

    def find_report(self, report_name):
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.id}/reports', headers=self.get_headers())
        json = handle_request(r)

        for r in json.get('value'):
            if r.get('name') == report_name:
                return Report(self, r)

    def publish_file(self, filepath, name, extension='.pbix', skipReports=False):
        params = {'datasetDisplayName': name + extension}
        if skipReports: params['skipReport'] = 'true'

        payload = {}
        with open(filepath, 'rb') as f:
            payload['file'] = open(filepath, 'rb')

        r = requests.post(f'https://api.powerbi.com/v1.0/myorg/groups/{self.id}/imports', params=params, headers=self.get_headers(), files=payload)
        json = handle_request(r)
        import_id = json.get('id')

        # Check whether import has finished, wait and retry if not
        while True:
            r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.id}/imports/{import_id}', headers=self.get_headers())
            json = handle_request(r)
            import_status = json.get('importState')

            if import_status == 'Succeeded':
                datasets = [self.get_dataset(d.get('id')) for d in json.get('datasets')]
                reports =  [self.get_report(r.get('id')) for r in json.get('reports')]

                return datasets, reports

            elif import_status == 'Publishing':
                time.sleep(10)
                continue

            else:
                print(f'Import ERROR: {json.get("error").get("code")} ({json.get("error").get("message")})')
                break

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

class Report:
    def __init__(self, workspace, report):
        self.workspace = workspace
        self.id = report['id']
        self.name = report['name']

    def repoint(self, dataset):
        payload = {
            'datasetId': dataset.id
        }
        r = requests.post(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/reports/{self.id}/Rebind', headers=self.workspace.get_headers(), json=payload)
        handle_request(r)
        self.dataset = dataset

    def clone(self, new_name):
        payload = {
            'name': new_name
        }
        r = requests.post(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/reports/{self.id}/Clone', headers=self.workspace.get_headers(), json=payload)
        json = handle_request(r)
        return Report(self.workspace, json)

    def download(self):
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/reports/{self.id}/Export', headers=self.workspace.get_headers())
        return r.content

    def delete(self):
        r = requests.delete(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/reports/{self.id}', headers=self.workspace.get_headers())
        handle_request(r)

class Portal:
    def __init__(self, env, token):
        self.token = token
        self.env = env
        self.api_url = f'https://diageo-eun-orion-datagovernanceapi-{env}.azurewebsites.net'
        self.get_reports()
        self.get_envs()

    def get_headers(self):
        return {'Authorization': f'Bearer {self.token.get_token()}'}

    def get_reports(self):
        r = requests.get(f'{self.api_url}/admin/report-detail', headers=self.get_headers())
        json = handle_request(r)

        self.reports = json
        return self.reports

    def get_report_configs(self):
        r = requests.get(f'{self.api_url}/admin/report-configuration', headers=self.get_headers())
        json = handle_request(r)

        self.report_configs = json
        return self.report_configs
    
    def get_menu_items(self):
        r = requests.get(f'{self.api_url}/admin/menu', headers=self.get_headers())
        json = handle_request(r)

        self.menu_items = json
        return self.menu_items

    def get_envs(self):
        r = requests.get(f'{self.api_url}/admin/report-environment', headers=self.get_headers())
        handle_request(r)

        self.envs = {}
        for e in r.json(): self.envs[e['Name']] = e
        return self.envs

    def sync_report(self, report, env_name):
        payload = {
            "ReportName": report.name,
            "ModelType": 'PBI' if report.dataset.has_rls else 'NoRLS',
            "PowerBIConfigurations": [{
                "EnvironmentId": self.envs[env_name]['Id'],
                "GroupId": report.workspace.id,
                "ReportId": report.id
            }]
        }

        matching_reports = [r for r in self.reports if r['ReportName'] == report.name]
        if len(matching_reports) > 0: # If report exists on Portal, add it to API call (to trigger update rather than insert)
            payload['PowerBIReportId'] = matching_reports[0]['Id']
        else:
            print(f'Adding {report.name} to {self.env} Portal')

        r = requests.put(f'{self.api_url}/admin/report-configuration', headers=self.get_headers(), json=payload)
        json = handle_request(r)
        return json

    def delete_report(self, report):
        r = requests.delete(f'{self.api_url}/admin/report-configuration/{report["Id"]}', headers=self.get_headers())
        handle_request(r)