from os import environ as env
from pbi import Token, Workspace

pbi_oauth_url = f'https://login.microsoftonline.com/{env.get("TENANTID")}/oauth2/v2.0/token'
pbi_token = Token(pbi_oauth_url, 'https://analysis.windows.net/powerbi/api/.default', env.get('PBI_SP'), env.get('PBI_SP_SECRET'))
workspace = Workspace(env.get('WORKSPACE_ID'), pbi_token)
config_workspace = Workspace(env.get('CONFIG_WORKSPACE_ID'), pbi_token) # Look here for the deployment aid
print(f'* Deploying to [{workspace.name}] workspace')

deploy(workspace, "data/Deployment Aid Model.pbix", ["data/Deployment Aid Report.pbix"], config_workspace=config_workspace)