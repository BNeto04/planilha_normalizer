import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def authenticate_google_sheets(credentials_path: str) -> object:
    """
    Authenticates with the Google Sheets API using service account credentials.

    Args:
        credentials_path (str): The file path to the service account credentials JSON file.

    Returns:
        object: An authorized Google Sheets API service object.

    Raises:
        FileNotFoundError: If the credentials file is not found.
        Exception: For other authentication or API build errors.
    """
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(f"Credentials file not found at: {credentials_path}")

    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=scopes)

        service = build('sheets', 'v4', credentials=creds)
        return service
    except HttpError as e:
        print(f"An API error occurred during authentication: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during authentication: {e}")
        raise