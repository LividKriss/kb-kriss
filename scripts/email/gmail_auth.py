#!/usr/bin/env python3
"""Gmail API access for the kb-kriss email scripts.

    gmail_auth.py authorize   one-time: opens the browser, Kriss consents, token goes to the Keychain
    gmail_auth.py check       loads the token from the Keychain and prints the mailbox it reaches

Other scripts call `gmail_service()`.

Secrets never touch the repo:
  - OAuth client JSON: ~/Library/Application Support/kb-kriss/client_secret*.json
  - Token (incl. refresh token): macOS Keychain, service "kb-kriss-gmail"

Run with the venv outside the repo:
  "~/Library/Application Support/kb-kriss/venv/bin/python" scripts/email/gmail_auth.py check
"""
import glob
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")  # system Python 3.9 / LibreSSL noise from google-auth and urllib3

import keyring
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

APP_DIR = os.path.expanduser("~/Library/Application Support/kb-kriss")
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.modify",  # labels (Mac agent, customs filing)
          "https://www.googleapis.com/auth/gmail.send"]    # forwards to the allowlist in gmail_tool.py
KEYCHAIN_SERVICE = "kb-kriss-gmail"
KEYCHAIN_ACCOUNT = "oauth-token"
EXPECTED_MAILBOX = "kristoffer@livid.no"


def client_secret_path():
    found = sorted(glob.glob(os.path.join(APP_DIR, "client_secret*.json")))
    if not found:
        sys.exit(f"No OAuth client JSON in {APP_DIR}. Download it from Google Cloud (Desktop app client).")
    if len(found) > 1:
        sys.exit(f"More than one client JSON in {APP_DIR}; keep only the current one: {found}")
    return found[0]


def save(creds):
    keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT, creds.to_json())


def load_credentials():
    raw = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT)
    if not raw:
        sys.exit("No Gmail token in the Keychain. Run: gmail_auth.py authorize")
    creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)
    if not creds.valid:
        creds.refresh(Request())
        save(creds)
    return creds


def gmail_service():
    return build("gmail", "v1", credentials=load_credentials(), cache_discovery=False)


def authorize():
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path(), SCOPES)
    # access_type=offline + prompt=consent so Google always returns a refresh token.
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not creds.refresh_token:
        sys.exit("Google returned no refresh token; nothing saved.")
    save(creds)
    check()


def check():
    profile = gmail_service().users().getProfile(userId="me").execute()
    print(f"OK: {profile['emailAddress']}, {profile['messagesTotal']} messages, "
          f"{profile['threadsTotal']} threads")
    if profile["emailAddress"].lower() != EXPECTED_MAILBOX:
        print(f"WARNING: expected {EXPECTED_MAILBOX}. Re-run authorize and pick the work account.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "authorize":
        authorize()
    elif cmd == "check":
        check()
    else:
        sys.exit(__doc__)
