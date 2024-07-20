import requests
import urllib.parse


class UpstoxAuth:
    def __init__(self, api_key, api_secret, redirect_uri):
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_uri = redirect_uri

    def get_login_url(self):
        base_url = "https://api.upstox.com/v2/login/authorization/dialog"
        params = {
            "response_type": "code",
            "client_id": self.api_key,
            "redirect_uri": self.redirect_uri,
        }
        login_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        return login_url

    def get_auth_code(self):
        login_url = self.get_login_url()
        print(f"Please go to this URL and authorize the app: {login_url}")
        auth_code = input("Enter the auth code from the URL after login: ")
        return auth_code

    def get_access_token(self, auth_code):
        url = "https://api.upstox.com/v2/login/authorization/token"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "code": auth_code,
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching access token: {response.json()}")
