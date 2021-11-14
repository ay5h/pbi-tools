import os
from src.pbi.token import Token
from src.pbi.api.tenant import Tenant

def test_workspace():
    tenant_id = os.environ.get("TENANTID")
    pbi_sp = os.environ.get("PBI_SP")
    pbi_sp_secret = os.environ.get("PBI_SP_SECRET")

    tenant = Tenant(tenant_id, pbi_sp, pbi_sp_secret)
    workspace_count = len(tenant.workspaces)
    
    assert workspace_count > 0, "No workspaces"