"""
Creates a Gmail API service client from credentials.
"""

from googleapiclient.discovery import build
from .user_consent import load_credentials_if_exists, run_console_authorization

def get_authenticated_credentials():
    """
    Return google.oauth2.credentials.Credentials.
    If token.json exists, load it; otherwise run local authorization flow.
    """
    creds = load_credentials_if_exists()
    if creds is None:
        creds = run_console_authorization()
    return creds

def build_gmail_service():
    """
    Returns an authorized Gmail API service object.
    """
    creds = get_authenticated_credentials()
    try:
        service = build("gmail", "v1", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Failed to build Gmail service: {e}")
    return service
