from google.oauth2 import service_account
from googleapiclient.discovery import build


# 1. Define the permissions (scopes) your script needs
# We are asking for access to both Google Drive and Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# 2. Tell Python where your downloaded credentials file lives
SERVICE_ACCOUNT_FILE = 'credentials.json'

def test_gsheet_connection(credentials_path: str, spreadsheet_id: str):
    # 3. Authenticate using the credentials and scopes
    creds = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )

    # 4. Build the API service connections
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    try:
        # Fetch the spreadsheet metadata
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        title = sheet_metadata.get('properties', {}).get('title')
        print(f"🎉 Success! Connected to spreadsheet: '{title}'")

    except Exception as e:
        print(f"❌ Error connecting to Google Sheets: {e}")
