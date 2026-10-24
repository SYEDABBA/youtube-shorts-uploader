import os
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Environment variables fetch kar rahe hain
CLIENT_ID = os.environ.get("YT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN")
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

print(f"Starting uploader script for Drive Folder ID: {DRIVE_FOLDER_ID}")

if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, DRIVE_FOLDER_ID]):
    print("Error: Missing required environment variables/secrets!")
    sys.exit(1)

# YouTube Video Title aur Description jo aapne diya hai
VIDEO_TITLE = "Allah Hu Akbar ❤️🕋 #shorts"

VIDEO_DESCRIPTION = """🤫 Allah Hu Akbar ❤️🕋
Allah is the Greatest 🤲✨
Keep Allah in your heart and faith in your soul. ❤️☝️
Like 👍 Share 🔄 Subscribe ❤️

#AllahHuAkbar​ #IslamicStatus​ #IslamicReels​ #IslamicShorts​ #MuslimUmmah​ #Allah​ #Deen​ #IslamicVibes​ #Muslim​ #ViralShorts​ #TrendingShorts​ #DripStatus​ #Shorts​ #YouTubeShorts​

Copyright Disclaimer: - Under section 107 of the copyright Act 1976, allowance is mad for FAIR USE for purpose such a as criticism, comment, news reporting, teaching, scholarship and research. Fair use is a use permitted by copyright statues that might otherwise be infringing.
Non- Profit, educational or personal use tips the balance in favor of FAIR USE."""

# Google API Credentials Setup
creds = Credentials(
    token=None,
    refresh_token=REFRESH_TOKEN,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    token_uri="https://oauth2.googleapis.com/token"
)

try:
    drive_service = build('drive', 'v3', credentials=creds)
    youtube_service = build('youtube', 'v3', credentials=creds)
    print("Google API Credentials authenticated successfully!")

    # Drive folder se video fetch karne ka query
    query = f"'{DRIVE_FOLDER_ID}' in parents and mimeType contains 'video/' and trashed = false"
    results = drive_service.files().list(
        q=query, pageSize=1, fields="files(id, name)"
    ).execute()
    files = results.get('files', [])

    if not files:
        print("No videos found in the specified Drive folder.")
        sys.exit(0)

    video_file = files[0]
    print(f"Found video to upload: {video_file['name']}")

    # Yahan par aapka YouTube upload execution logic aayega (jo already aapki purani script me tha)
    print("Ready for upload with your custom title and description!")

except Exception as e:
    print(f"An error occurred during execution: {e}")
    sys.exit(1)
