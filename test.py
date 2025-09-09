import requests
import json
import time
import os
from bs4 import BeautifulSoup


API_URL = "https://rooms.vestide.nl/api/accommodation/getlivingspaces/?LanguageCode=en&Skip=0&Take=999" # to change
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1404064271314190336/_AkqNou8uOAJM6ax74y5yrq8yKPyxLJoF3CU3LecOoOK8iUbwqbaCRTkBn-HBBXPKj79"
CHECK_INTERVAL = 10  # seconds (5 minutes)
SEEN_FILE = "seen_listings.json"
LOGIN_URL = "https://www.pararius.com/login-email"
USERNAME = "gyerek116@gmail.com"
PASSWORD = "FASZFASZ!@#123a"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.pararius.com/english"
}

session = requests.Session()

def login():
    # Step 1: Get login page
    print("LOGIN")
    r = session.get(LOGIN_URL, headers=HEADERS)
    r.raise_for_status()

    # Step 2: Parse hidden token
    soup = BeautifulSoup(r.text, "html.parser")
    token = soup.find("input", {"name": "_token"})["value"]

    # Step 3: Send login POST
    payload = {
        "_token": token,
        "email": USERNAME,
        "password": PASSWORD,
    }
    resp = session.post(LOGIN_URL, data=payload, headers=HEADERS, allow_redirects=False)

    if resp.status_code in (200, 302):
        print("✅ Logged in successfully")
    else:
        print("❌ Login failed:", resp.status_code, resp.text[:200])


def main():
    print("Test")
    login()


if __name__ == "__main__":
    main()
