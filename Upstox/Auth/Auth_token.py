import requests
import configparser
import os

# Function to read properties from the application.properties file
def read_properties(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config['DEFAULT']

# Step 1: Get the login URL
def get_login_url():
    login_url = f'https://api.upstox.com/index/dialog/authorize?apiKey={API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code'
    return login_url

# Step 2: Extract the auth code from the redirect URL
# You need to manually visit the login URL, log in, and get the auth code from the redirect URL
def get_auth_code():
    login_url = get_login_url()
    print(f"Please go to this URL and authorize the app: {login_url}")
    auth_code = input("Enter the auth code from the URL after login: ")
    return auth_code

# Step 3: Use the auth code to get the access token
def get_access_token(auth_code):
    # Read properties from the application.properties file
    properties_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'application.properties')
    properties = read_properties(properties_path)

    API_KEY = properties.get('api_key')
    API_SECRET = properties.get('api_secret')
    REDIRECT_URI = properties.get('redirect_uri')
    
    url = 'https://api.upstox.com/index/oauth/token'
    payload = {
        'code': auth_code,
        'client_id': API_KEY,
        'client_secret': API_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching access token: {response.json()}")

