from datetime import datetime, timedelta
import requests
from .tools import handle_request
        
class Token:
    def __init__(self, url, scope, principal, secret):
        self.url = url
        self.scope = scope
        self.principal = principal
        self.secret = secret
        self.refresh()

    def refresh(self):
        payload = {
            'grant_type': 'client_credentials',
            'scope': self.scope,
            'client_id': self.principal,
            'client_secret': self.secret
        }
        r = requests.post(self.url, payload)
        handle_request(r)

        self.__token = r.json()['access_token']
        self.__token_expiry = datetime.now() + timedelta(minutes = 30)

    def get_token(self):
        if not self.__token or self.__token_expiry < datetime.now():
            self.refresh()
        return self.__token