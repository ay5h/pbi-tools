import requests
from pbi.tools import handle_request


class Report:
    """An object representing a Power BI report.
    You can find the GUID by going to the report and inspecting the URL:

            `https://app.powerbi.com/groups/7b0ce7b6-5055-45b2-a15b-ffeb34a85368/reports/**4702db31-bc75-422c-92b4-b6a0809b0f1a**/ReportSection`

    :param workspace: :class:`~Workspace` object representing the PBI workspace that the report lives in
    :param report: a dictionary of attributes expected to include ``id`` and ``name``
    :return: :class:`~Report` object
    """

    def __init__(self, workspace, report):
        self.workspace = workspace
        self.id = report["id"]
        self.name = report["name"]

    def repoint(self, dataset):
        """Repoint this report to a new model.

        :param dataset: the new model
        """

        payload = {"datasetId": dataset.id}
        r = requests.post(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/reports/{self.id}/Rebind",
            headers=self.workspace.tenant.token.get_headers(),
            json=payload,
        )
        handle_request(r)
        self.dataset = dataset

    def clone(self, new_name):
        """Make a copy of this report

        :param new_name: The new report name
        :return: newly created :class:`~Report` object
        """

        payload = {"name": new_name}
        r = requests.post(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/reports/{self.id}/Clone",
            headers=self.workspace.tenant.token.get_headers(),
            json=payload,
        )
        json = handle_request(r)

        return Report(self.workspace, json)  # Return new report object

    def rename(self, new_name):
        """Rename this report.
        Due to limitations in the PBI REST API, this actually creates a copy of the report and deletes the old one, returning a reference to the new report.

        **Warning**: The report GUID will change as a result of calling this method.

        :param new_name: The new report name
        :return: newly created :class:`~Report` object
        """

        new_report = self.clone(
            new_name
        )  # Create new report object (API doesn't support rename)
        self.delete()  # Delete old report

        return new_report

    def download(self):
        """Download this report from the workspace to the current working directory."""

        r = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/reports/{self.id}/Export",
            headers=self.workspace.tenant.token.get_headers(),
        )
        return r.content

    def delete(self):
        """Delete this report from the workspace."""

        r = requests.delete(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace.id}/reports/{self.id}",
            headers=self.workspace.tenant.token.get_headers(),
        )
        handle_request(
            r, allowed_codes=[404]
        )  # Don't fail it dataset has already been deleted
