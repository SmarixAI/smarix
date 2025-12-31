import json
import os
import webbrowser
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
TOKEN_FILE = Path(os.getenv("GMAIL_TOKEN_PATH", "token.json"))
OPEN_BROWSER = os.getenv("GMAIL_OPEN_BROWSER", "0") == "1"
FORCE_REAUTH_ENV = os.getenv("GMAIL_FORCE_REAUTH", "0") == "1"
REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")


def ensure_env_creds_exist():
    missing = []
    if not CLIENT_ID:
        missing.append("GMAIL_CLIENT_ID")
    if not CLIENT_SECRET:
        missing.append("GMAIL_CLIENT_SECRET")
    if missing:
        raise EnvironmentError(
            f"Missing environment variables: {', '.join(missing)}.\n"
            "Set them and re-run. Example:\n"
            "  export GMAIL_CLIENT_ID='...'\n"
            "  export GMAIL_CLIENT_SECRET='...'\n"
            "Optional: export GMAIL_FORCE_REAUTH='1' to force reauth."
        )


def build_installed_flow() -> InstalledAppFlow:
    ensure_env_creds_exist()
    client_config = {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
        }
    }
    return InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)


def save_credentials(creds: Credentials):
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(data, indent=2))
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except Exception:
        pass
    print(f"[GMAIL] Saved credentials -> {TOKEN_FILE.resolve()}")


def load_credentials_if_exists() -> Optional[Credentials]:
    if not TOKEN_FILE.exists():
        return None
    try:
        data = json.loads(TOKEN_FILE.read_text())
        creds = Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=data.get("scopes"),
        )
        return creds
    except Exception as e:
        print(f"[GMAIL] Failed to load token file {TOKEN_FILE}: {e}")
        return None


def _maybe_force_delete_token(force_reauth_flag: bool):
    """
    Delete token file if force_reauth_flag True.
    """
    if force_reauth_flag and TOKEN_FILE.exists():
        try:
            TOKEN_FILE.unlink()
            print(f"[GMAIL] Existing token removed due to force reauth -> {TOKEN_FILE}")
        except Exception as e:
            print(f"[GMAIL] Failed to remove token file: {e}")


def run_console_authorization() -> Credentials:
    """
    Manual authorization flow that forces account chooser and uses a consistent redirect_uri.
    - Prints an auth URL (optionally opens it)
    - User approves and copies the code
    - Exchanges code for tokens using flow.fetch_token(code=code) (do NOT pass redirect_uri twice)
    """
    flow = build_installed_flow()

    flow.redirect_uri = REDIRECT_URI

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="select_account consent"
    )

    print("\n" + "=" * 60)
    print("       Gmail Authorization Required")
    print("=" * 60)
    print("\nOpen the URL below in your browser (incognito recommended):\n")
    print(auth_url)
    print("\nAfter approving, copy the code Google shows and paste it below.\n")

    if OPEN_BROWSER:
        try:
            webbrowser.open(auth_url, new=2)
            print("(Opened URL in your default browser)\n")
        except Exception:
            pass

    code = input("Enter authorization code: ").strip()
    if not code:
        raise ValueError("No authorization code provided.")

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        msg = (
            f"Failed to fetch token: {e}\n\n"
            "Likely causes & fixes:\n"
            " - You used an auth URL generated for a different redirect URI than the one the client supports.\n"
            " - The 'urn:ietf:wg:oauth:2.0:oob' (OOB) flow is disabled for your OAuth client in Google Cloud.\n\n"
            "Fixes:\n"
            " 1) Set env var GMAIL_REDIRECT_URI='http://localhost' and re-run the script. Also ensure your\n"
            "    OAuth client in Google Cloud Console has http://localhost as an authorized redirect URI.\n"
            "    Then re-run so a NEW auth URL is generated and use the new code.\n"
            " 2) Or delete the saved token file (GMAIL_TOKEN_PATH) and try again (use GMAIL_FORCE_REAUTH=1 to automate).\n"
        )
        raise RuntimeError(msg)

    creds = flow.credentials
    if not creds:
        raise RuntimeError("Failed to obtain credentials after authorization.")
    save_credentials(creds)
    print("\n✓ [GMAIL] Authorization successful!")
    return creds


def get_or_authorize_credentials(force_reauth: bool = False) -> Credentials:
    """
    Load existing credentials or prompt manual auth.
    If force_reauth True (or GMAIL_FORCE_REAUTH=1), deletes existing token and reauthorizes.
    """
    if FORCE_REAUTH_ENV:
        print("[GMAIL] GMAIL_FORCE_REAUTH env var is set -> forcing reauthorization.")
        _maybe_force_delete_token(True)
    elif force_reauth:
        _maybe_force_delete_token(True)

    creds = load_credentials_if_exists()
    if creds:
        print(f"[GMAIL] Loaded existing credentials from {TOKEN_FILE}.")
        return creds

    # No saved creds -> run manual flow
    return run_console_authorization()
