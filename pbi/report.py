import requests
from .tools import handle_request
        
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

        return Report(self.workspace, json) # Return new report object

    def rename(self, new_name):
        new_report = self.clone(new_name) # Create new report object (API doesn't support rename)
        self.delete() # Delete old report

        return new_report

    def download(self):
        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/reports/{self.id}/Export', headers=self.workspace.get_headers())
        return r.content

    def delete(self):
        r = requests.delete(f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/reports/{self.id}', headers=self.workspace.get_headers())
        handle_request(r)