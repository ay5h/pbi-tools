import os
from pbi.token import Token
from pbi.workspace import Workspace

tenant_id = os.environ.get('TENANTID')
workspace_id = os.environ.get('WORKSPACE_ID')
pbi_sp = os.environ.get('PBI_SP')
pbi_sp_secret = os.environ.get('PBI_SP_SECRET')

oauth_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
pbi_token = Token(oauth_url, 'https://analysis.windows.net/powerbi/api/.default', pbi_sp, pbi_sp_secret)

workspace = Workspace(workspace_id, pbi_token)

for dataset in workspace.datasets:
    dataset.get_datasources()