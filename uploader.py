import os
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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

# Tumhara YouTube Video Title aur Description
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
    file_id = video_file['id']
    file_name = video_file['name']
    print(f"Found video to upload: {file_name} (ID: {file_id})")

    # Download video locally from Google Drive
    local_video_path = "temp_video.mp4"
    request = drive_service.files().get_media(fileId=file_id)
    with open(local_video_path, "wb") as f:
        f.write(request.execute())
    print("Video downloaded locally successfully!")

    # Upload video to YouTube
    body = {
        'snippet': {
            'title': VIDEO_TITLE,
            'description': VIDEO_DESCRIPTION,
            'tags': ['AllahHuAkbar', 'IslamicStatus', 'IslamicShorts', 'Shorts'],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(local_video_path, chunksize=-1, resumable=True)
    print("Uploading video to YouTube...")

    request = youtube_service.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print(f"Video uploaded successfully! Video ID: {response.get('id')}")

    # Processed video ko Google Drive se delete karna taaki dubara upload na ho
    drive_service.files().delete(fileId=file_id).execute()
    print("Processed video deleted from Google Drive folder.")

    # Local temporary file clean up
    if os.path.exists(local_video_path):
        os.remove(local_video_path)

except Exception as e:
    print(f"An error occurred during execution: {e}")
    sys.exit(1)
