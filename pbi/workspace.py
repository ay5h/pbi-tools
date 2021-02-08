import time
import requests
from .tools import handle_request
from .report import Report
from .dataset import Dataset
        
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