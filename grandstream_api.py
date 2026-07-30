"""
grandstream_api.py

Standalone authentication module for the GWN.Cloud API.
Requests an access token using APP_ID / SECRET_KEY read from environment
variables (never hardcoded), and prints the raw response.

CONFIRMED WORKING FORMAT (tested against the live API):
    GET https://www.gwn.cloud/oauth/token
        ?grant_type=client_credentials
        &client_id={APP_ID}
        &client_secret={SECRET_KEY}

    Returns: {"access_token": "...", "token_type": "bearer",
              "expires_in": 3599, "scope": "read write"}

    Token expires in ~1 hour (3599 seconds) - callers must request a new
    one periodically, not just once at startup.

Setup:
    1. Enable "API Developer Mode" on GWN.Cloud (Others -> API Developer)
       and copy your App ID + Secret Key from there.
    2. Put them in a .env file:
         GWN_APP_ID=your_app_id
         GWN_SECRET_KEY=your_secret_key
    3. pip install requests python-dotenv
    4. python grandstream_api.py
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

GWN_APP_ID = os.environ.get("GWN_APP_ID")
GWN_SECRET_KEY = os.environ.get("GWN_SECRET_KEY")

GWN_BASE_URL = os.environ.get("GWN_BASE_URL", "https://www.gwn.cloud")
GWN_TOKEN_URL = f"{GWN_BASE_URL}/oauth/token"


def get_access_token():
    """
    Requests an access token from the GWN.Cloud API using APP_ID and
    SECRET_KEY from environment variables. Returns the parsed JSON
    response.
    """

    if not GWN_APP_ID or not GWN_SECRET_KEY:
        raise RuntimeError(
            "GWN_APP_ID and GWN_SECRET_KEY must be set in your .env file "
            "before running this script."
        )

    params = {
        "grant_type": "client_credentials",
        "client_id": GWN_APP_ID,
        "client_secret": GWN_SECRET_KEY,
    }

    response = requests.get(GWN_TOKEN_URL, params=params, timeout=30)

    try:
        body = response.json()
    except ValueError:
        body = {"raw_text": response.text}

    return {
        "status_code": response.status_code,
        "body": body,
    }


if __name__ == "__main__":
    print(f"Requesting access token from: {GWN_TOKEN_URL}")

    try:
        result = get_access_token()
        print(f"HTTP status: {result['status_code']}")
        print("Response body:")
        print(result["body"])

        if result["status_code"] == 200 and result["body"].get("access_token"):
            print("\n✅ SUCCESS - got an access token.")
        else:
            print("\n⚠️  Got a response, but no access_token in it.")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed before getting a response: {e}")
    except RuntimeError as e:
        print(f"\n❌ {e}")
