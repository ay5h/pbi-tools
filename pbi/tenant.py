import time
import requests
from os import path

from .token import Token
from .report import Report
from .dataset import Dataset

class Tenant:
    """An object representing an Azure tenant.
    
    :param id: the Azure tenant GUID
    :param principal: service principal GUID
    :param secret: associated secret value to authenticate the service principal
    :return: :class:`~Tenant` object
    """

    def __init__(self, id, sp, secret):
        pbi_oauth_url = f'https://login.microsoftonline.com/{id}/oauth2/v2.0/token'
        scope = 'https://analysis.windows.net/powerbi/api/.default'
        self.token = Token(pbi_oauth_url, scope, sp, secret)

    def get_headers(self):
        return {'Authorization': f'Bearer {self.token.get_token()}'}
