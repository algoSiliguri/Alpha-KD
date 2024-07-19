from Auth import get_auth_code, get_access_token

if __name__ == "__main__":
    auth_code = get_auth_code()
    token_response = get_access_token(auth_code)
    print("Access Token Response:")
    print(token_response)