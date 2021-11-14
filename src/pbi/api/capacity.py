import requests

from pbi.token import Token
from pbi.token import handle_request


class Capacity:
    """An object representing a Power BI capacity.

    :param tenant_id: the Azure tenant GUID
    :param subscription_id: the Azure subscription GUID
    :param resource_group_name: the Azure resource group name
    :param capacity_name: the Power BI capacity name
    :param principal: service principal GUID
    :param secret: associated secret value to authenticate the service principal
    :return: :class:`~Capacity` object
    """

    def __init__(
        self,
        tenant_id,
        subscription_id,
        resource_group_name,
        capacity_name,
        principal,
        secret,
    ):
        self.tenant_id = tenant_id
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.capacity_name = capacity_name

        pbi_oauth_url = (
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        )
        scope = "https://management.azure.com/.default"
        self.token = Token(pbi_oauth_url, scope, principal, secret)

        self.skus = self.get_skus()

    def get_skus(self):
        """Fetch a list of all available SKUs for this capacity.

        :return: Dictionary of SKUs by name
        """

        r = requests.get(
            f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}/providers/Microsoft.PowerBIDedicated/capacities/{self.capacity_name}/skus?api-version=2017-10-01",
            headers=self.token.get_headers(),
        )
        response = handle_request(r)
        skus = {x["sku"]["name"]: x["sku"] for x in response["value"]}

        return skus

    def change_sku(self, sku_name):
        """Update capacity with the given SKU."""

        payload = {"sku": self.skus.get(sku_name)}  # TODO: Handle SKU not found event
        r = requests.patch(
            f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}/providers/Microsoft.PowerBIDedicated/capacities/{self.capacity_name}?api-version=2017-10-01",
            json=payload,
            headers=self.token.get_headers(),
        )
        handle_request(r)  # TODO: Handle errors
