import os
from config_reader import ConfigReader
from upstox_auth import UpstoxAuth


def main():
    properties_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "application.properties"
    )
    config_reader = ConfigReader(properties_path)

    api_key = config_reader.get_property("api_key")
    api_secret = config_reader.get_property("api_secret")
    redirect_uri = config_reader.get_property("redirect_uri")

    upstox_auth = UpstoxAuth(api_key, api_secret, redirect_uri)
    auth_code = upstox_auth.get_auth_code()
    access_token = upstox_auth.get_access_token(auth_code)
    print(f"Access Token: {access_token}")


if __name__ == "__main__":
    main()
