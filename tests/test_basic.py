import os
import pytest

from pbi.api import Tenant, Workspace
from pbi.deploy import deploy

@pytest.fixture(autouse=True)
def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)

@pytest.fixture
def tenant():
    tenant_id = os.environ.get("TENANTID")
    pbi_sp = os.environ.get("PBI_SP")
    pbi_sp_secret = os.environ.get("PBI_SP_SECRET")

    tenant = Tenant(tenant_id, pbi_sp, pbi_sp_secret)
    return tenant

@pytest.fixture
def config_workspace(tenant: Tenant):
    config_workspace_id = os.environ.get("CONFIG_WORKSPACE_ID")
    tenant.set_config_workspace(config_workspace_id)
    config_workspace = tenant.config_workspace
    
    return config_workspace

@pytest.fixture
def test_workspace(config_workspace: Workspace):
    test_workspace_id = os.environ.get("WORKSPACE_ID")
    test_workspace = Workspace(config_workspace.tenant, test_workspace_id)

    # Clean up test environment
    test_models = test_workspace.get_datasets()
    for model in test_models:
        model.delete()

    return test_workspace

def test_tenant(tenant: Tenant):
    assert tenant, "Cannot connect to tenant"

def test_config_workspace(config_workspace: Workspace):
    assert config_workspace, "Cannot find config_workspace"

def test_deployment_aid(config_workspace: Workspace):
    aid_model, aid_report = config_workspace.tenant.get_deployment_aids()

    assert aid_model and aid_report, "Cannot find deployment aid"

def test_deploy(test_workspace: Workspace):
    root = "fixtures/Deployment Root/Model 1"
    test_workspace.deploy(f"{root}/Model.pbix", [f"{root}/Report 1.pbix", f"{root}/Report 2.pbix"])

    models = test_workspace.get_datasets()
    reports = test_workspace.get_reports()
    
    assert len(models) == 1 and len(reports) == 2, f"Deployment failed. Found {len(models)} models and {len(reports)} reports"

def test_deploy_root(test_workspace: Workspace):
    deploy("fixtures/Deployment Root", test_workspace)

    models = test_workspace.get_datasets()
    reports = test_workspace.get_reports()

    assert len(models) == 2 and len(reports) == 4, f"Deployment failed. Found {len(models)} models and {len(reports)} reports"
