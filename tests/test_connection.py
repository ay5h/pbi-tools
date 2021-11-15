import os
from pbi.api.tenant import Tenant
from pbi.api.workspace import Workspace

def get_tenant():
    tenant_id = os.environ.get("TENANTID")
    pbi_sp = os.environ.get("PBI_SP")
    pbi_sp_secret = os.environ.get("PBI_SP_SECRET")

    tenant = Tenant(tenant_id, pbi_sp, pbi_sp_secret)
    return tenant

def get_workspace():
    tenant = get_tenant()
    workspace_id = os.environ.get("WORKSPACE_ID")
    
    workspace = Workspace(tenant, workspace_id)
    return workspace

def test_connect_tenant():
    tenant = get_tenant()
    workspace_count = len(tenant.workspaces)
    
    assert workspace_count > 0, "No workspaces"

def test_connect_workspace():
    workspace = get_workspace()

    assert workspace, "Cannot connect to workspace"
