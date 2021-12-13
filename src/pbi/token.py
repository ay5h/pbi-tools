from datetime import datetime, timedelta
import requests
from .tools import handle_request


class Token:
    """An object representing an oauth token. Currently, authentication must use a service principal.

    This class is used by :class:`~Workspace` to authenticate with the Power BI service. It may also be used to create oauth tokens to authenticate against data sources.

    :param url: the url responsible for providing the oauth token
    :param scope: scope string as defined by the oauth protocol
    :param principal: service principal GUID
    :param secret: associated secret value to authenticate the service principal
    :return: :class:`~Token` object
    """

    def __init__(self, url, scope, principal, secret):
        self.url = url
        self.scope = scope
        self.principal = principal
        self.secret = secret
        self.refresh()

    def refresh(self):
        """Renew the token using same credentials."""

        payload = {
            "grant_type": "client_credentials",
            "scope": self.scope,
            "client_id": self.principal,
            "client_secret": self.secret,
        }
        r = requests.post(self.url, payload)
        handle_request(r)

        self.__token = r.json()["access_token"]
        self.__token_expiry = datetime.now() + timedelta(minutes=30)

    def get_token(self):
        """Returns a token string, renewing it first with the oauth provider if it has been more the 30 minutes since the last renewal.

        Using this method means you don't have to worry about token expiry (except see :meth:`~Datasource.update_credentials` for issues with data refresh timeouts).

        :return: oauth token string
        """

        if not self.__token or self.__token_expiry < datetime.now():
            self.refresh()
        return self.__token

    def get_headers(self):
        """Returns a response header containing the Bearer token.

        :return: response header as JSON
        """
        return {"Authorization": f"Bearer {self.get_token()}"}
