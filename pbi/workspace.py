import time
import requests
import os

from .report import Report
from .dataset import Dataset
from .tools import handle_request, get_connection_string, check_file_modified, rebind_report

AID_REPORT_NAME = 'Deployment Aid Report'
        
class Workspace:
    def __init__(self, id, token, stage=None):
        self.id = id
        self.token = token

        r = requests.get(f'https://api.powerbi.com/v1.0/myorg/groups?$filter=contains(id,\'{self.id}\')', headers=self.get_headers())
        handle_request(r)
        self.name = r.json()['value'][0]['name']

        self.get_datasets()
        self.get_reports()
    
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

    def publish_file(self, filepath, name, skipReports=False):
        params = {'datasetDisplayName': name}
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

    def refresh_datasets(self, credentials=None):
        error = False
        datasets = [d for d in self.datasets if 'Deployment Aid' not in d.name]
        
        for dataset in datasets:
            try:
                if dataset.get_refresh_state() == 'Unknown': # Don't trigger refresh if model is already refreshing
                    print(f'** [{dataset.name}] is already refreshing')
                else:
                    print(f'** Reconfiguring [{dataset.name}]')
                    dataset.take_ownership() # In case someone manually took control post deployment

                    if credentials:
                        print(f'*** Reauthenticating data sources...') # Reauthenticate as tokens obtained during deployment will have expired
                        dataset.authenticate(credentials)

                    print(f'*** Starting refresh...') # We check back later for completion
                    dataset.trigger_refresh()

            except SystemExit as e:
                print(f'!! ERROR. Triggering refresh failed for [{dataset.name}]. {e}')
                error = True

        print('* Waiting for models to finish refreshing...')
        for dataset in datasets:
            try:
                refresh_status = dataset.get_refresh_state(wait=True) # Wait for each refresh to complete
                if refresh_status == 'Completed':
                    print(f'** Refresh complete for [{dataset.name}]')
                else:
                    raise SystemExit(refresh_status)

            except SystemExit as e:
                print(f'!! ERROR. Refresh failed for [{dataset.name}]. {e}')
                error = True

        return not error

    def deploy(self, dataset_filepath, report_filepaths, dataset_params=None, credentials=None, force_refresh=False, on_report_success=None, name_builder=None, config_workspace=None, **kwargs):
        # 1. Get dummy connections string from 'aid report' (use config workspace if given, else content workspace)
        aid_report = (config_workspace or self).find_report(AID_REPORT_NAME) # Find aid report to get new dataset connection string
        if aid_report is None:
            raise SystemExit('ERROR: Cannot find Deployment Aid Report')

        with open(AID_REPORT_NAME, 'wb') as report_file: # Get connection string from aid report
            report_file.write(aid_report.download())
        connection_string = get_connection_string(AID_REPORT_NAME)

        # 2. Publish dataset or get existing dataset (if unchanged and current)
        dataset_name = name_builder(dataset_filepath, **kwargs) if name_builder else os.path.basename(dataset_filepath) # Allow custom name formation, default to filename
        matching_datasets = [d for d in self.datasets if d.name == os.path.splitext(dataset_name)[0]] # Look for existing dataset
        dataset_modified = check_file_modified(dataset_filepath)

        if matching_datasets and not dataset_modified and not force_refresh: # Only publish dataset if it's been updated (or override used):
            dataset = matching_datasets.pop() # Get the latest dataset
            print(f'** Using existing dataset [{dataset.name}]')
        else:
            print(f'** Found {len(matching_datasets)} matching datasets on service. Model modified in repo? {dataset_modified}. Refresh forced? {force_refresh}')
            print(f'** Publishing dataset [{dataset_filepath}] as [{dataset_name}]...')
            new_datasets, new_reports = self.publish_file(dataset_filepath, dataset_name, skipReports=True)
            dataset = new_datasets.pop()

        # 3. Update params and credentials, then refresh (unless current)
        if dataset.get_refresh_state() not in ('Completed', 'Unknown'): # If we're using a valid exising dataset, don't touch it
            dataset.take_ownership() # Publishing does not change ownership, so make sure we own it before continuing

            print('*** Updating parameters...')
            param_keys = [p['name'] for p in dataset.get_params()]
            params = [{'name': k, 'newValue': v} for k, v in dataset_params.items() if k in param_keys] # Only try to update params that are defined for this dataset
            if params: dataset.update_params({'updateDetails': params})

            print('*** Authenticating...')
            dataset.authenticate(credentials)

            print('*** Triggering refresh') # We check back later for completion
            dataset.trigger_refresh()
            
            # 4. Wait for refresh to complete (stop on error)
            time.sleep(5) # Wait a moment before continuing as the refresh takes doesn't register immediately (if not, we might not see the refresh status when we check)
            refresh_state = dataset.get_refresh_state(wait=True) # Wait for any dataset refreshes to finish before continuing
            if refresh_state == 'Completed':
                print('*** Dataset refreshed') # Don't report completed refresh if we used an existing dataset
            else:
                raise SystemExit(f'Refresh failed: {refresh_state}')

        # 5. Publish reports (using dummy connection string initially)
        for filepath in report_filepaths: # Import report files
            report_name = name_builder(filepath, **kwargs) if name_builder else os.path.basename(filepath) # Allow custom name formation, default to filename
            matching_reports = [r for r in self.reports if r.name == os.path.splitext(report_name)[0]] # Look for existing reports

            print(f'** Publishing report [{filepath}] as [{report_name}]...') # Alter PBIX file with dummy dataset, in case dataset used during development has since been deleted (we repoint once on service)
            rebind_report(filepath, connection_string)
            new_datasets, new_reports = self.publish_file(filepath, report_name)

            # 6. Repoint to refreshed model and update Portals (if given)
            for report in new_reports:
                report.repoint(dataset) # Once published, repoint from dummy to new dataset
                if on_report_success: on_report_success(report, **kwargs) # Perform any final post-deploy actions

            # 7. Delete old reports
            for old_report in matching_reports:
                print(f'** Deleting old report [{old_report.name}]')
                old_report.delete()

        # 8. Delete old models
        for old_dataset in matching_datasets:
            print(f'** Deleting old dataset [{old_dataset.name}]')
            old_dataset.delete()