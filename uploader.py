import os
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Dynamic Client Credentials Selection
# Agar CLIENT2_CLIENT_ID maujood hai toh Client 2 ke credentials uthayega, warna Client 1 ke.
CLIENT_ID = os.environ.get("CLIENT2_CLIENT_ID") or os.environ.get("YT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT2_CLIENT_SECRET") or os.environ.get("YT_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("CLIENT2_REFRESH_TOKEN") or os.environ.get("YT_REFRESH_TOKEN")
DRIVE_FOLDER_ID = os.environ.get("CLIENT2_DRIVE_FOLDER_ID") or os.environ.get("DRIVE_FOLDER_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

print(f"Starting uploader script for Target Folder ID: {DRIVE_FOLDER_ID}")

if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, DRIVE_FOLDER_ID]):
    print("Error: Missing required environment variables/secrets!")
    sys.exit(1)

# Google API Credentials Setup
creds = Credentials(
    token=None,
    refresh_token=REFRESH_TOKEN,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    token_uri="https://oauth2.googleapis.com/token"
)

try:
    # Google Drive aur YouTube service initialize karna
    drive_service = build('drive', 'v3', credentials=creds)
    youtube_service = build('youtube', 'v3', credentials=creds)
    print("Google API Credentials authenticated successfully!")

    # Drive folder se files fetch karne ka logic
    query = f"'{DRIVE_FOLDER_ID}' in parents and mimeType contains 'video/' and trashed = false"
    results = drive_service.files().list(
        q=query, pageSize=1, fields="files(id, name)"
    ).execute()
    files = results.get('files', [])

    if not files:
        print("No videos found in the specified Drive folder.")
        sys.exit(0)

    print(f"Found video to process: {files[0]['name']}")
    # Yahan tumhara baaki uploading/processing code chalega...

except Exception as e:
    print(f"An error occurred during execution: {e}")
    sys.exit(1)
