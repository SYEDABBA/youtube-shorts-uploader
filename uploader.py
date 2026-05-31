import os
import random
import sys
from groq import Groq
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN")
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET")
GD_REFRESH_TOKEN = os.environ.get("GD_REFRESH_TOKEN")

FOLDER_IDS = ["16F9CmM4abxAvX_nUPyAKXSSl94T0xUMV", "1dVjqB7m_IKHIZ2-PN8PmNiXhC4jRVFbU"]

if not all([GROQ_API_KEY, YT_REFRESH_TOKEN, YT_CLIENT_ID, YT_CLIENT_SECRET, GD_REFRESH_TOKEN]):
    print("❌ Error: Missing required environment secrets!")
    sys.exit(1)

# Cleaned Groq Client Initialization to avoid version mismatch proxies error
groq_client = Groq(api_key=GROQ_API_KEY.strip())

def get_video_from_drive():
    print("📥 Connecting to Google Drive...")
    creds = Credentials(
        token=None,
        refresh_token=GD_REFRESH_TOKEN.strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YT_CLIENT_ID.strip(),
        client_secret=YT_CLIENT_SECRET.strip()
    )
    drive_service = build('drive', 'v3', credentials=creds)
    selected_folder = random.choice(FOLDER_IDS)
    query = f"'{selected_folder}' in parents and (mimeType contains 'video/mp4' or mimeType contains 'video/mkv') and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    if not items: 
        print("❌ Drive folder me koi video nahi mili!")
        return None, None
    random_video = random.choice(items)
    video_id = random_video['id']
    video_name = random_video['name']
    video_path = "temp_video.mp4"
    print(f"✅ Video found: {video_name}. Downloading...")
    request = drive_service.files().get_media(fileId=video_id)
    with open(video_path, "wb") as f: f.write(request.execute())
    return video_path, video_name

def generate_seo(video_name):
    print("🤖 Generating viral SEO tags with Groq AI...")
    prompt = f"You are an expert YouTube SEO manager. Generate a viral YouTube Shorts SEO pack for a video named '{video_name}'. Output format strictly: TITLE: [title with #shorts] DESCRIPTION: [desc with hashtags] TAGS: [comma separated]"
    try:
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=[{"role": "user", "content": prompt}], 
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"⚠️ Groq AI API warning: {e}. Using safe fallback SEO.")
        return None

def upload_to_youtube(video_path, seo_data):
    print("📤 Uploading video to YouTube Channel...")
    creds = Credentials(
        token=None,
        refresh_token=YT_REFRESH_TOKEN.strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YT_CLIENT_ID.strip(),
        client_secret=YT_CLIENT_SECRET.strip()
    )
    youtube = build('youtube', 'v3', credentials=creds)
    lines = seo_data.split('\n')
    title, description, tags = "Trending YouTube Short #shorts", "Auto Uploaded by YUGRAAL", ["shorts"]
    for line in lines:
        if line.strip().startswith("TITLE:"): title = line.replace("TITLE:", "").strip()
        elif line.strip().startswith("DESCRIPTION:"): description = line.replace("DESCRIPTION:", "").strip()
        elif line.strip().startswith("TAGS:"): tags = line.replace("TAGS:", "").strip().split(",")
    body = {
        'snippet': {'title': title[:100], 'description': description, 'tags': [t.strip() for t in tags if t.strip()], 'categoryId': '24'},
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    response = request.execute()
    print(f"🎉 SUCCESS! Video uploaded successfully. Video ID: {response.get('id')}")

def main():
    print("🚀 Starting automated upload system...")
    video_path, video_name = get_video_from_drive()
    if not video_path: return
    
    seo = generate_seo(video_name) or "TITLE: Viral Manga Explanations #shorts\nDESCRIPTION: #shorts #viral #manga\nTAGS: shorts, manga"
    
    try: 
        upload_to_youtube(video_path, seo)
    except Exception as e:
        print(f"❌ YouTube upload failed with error: {e}")
    finally:
        if os.path.exists(video_path): 
            os.remove(video_path)
            print("🧹 Temporary video file cleaned up.")

if __name__ == "__main__":
    main()
