import os
import random
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN")
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET")
GD_REFRESH_TOKEN = os.environ.get("GD_REFRESH_TOKEN")

FOLDER_IDS = ["16F9CmM4abxAvX_nUPyAKXSSl94T0xUMV", "1dVjqB7m_IKHIZ2-PN8PmNiXhC4jRVFbU"]

if not all([YT_REFRESH_TOKEN, YT_CLIENT_ID, YT_CLIENT_SECRET, GD_REFRESH_TOKEN]):
    print("❌ Error: Missing required environment secrets!")
    sys.exit(1)

# Fixed Title
FIXED_TITLE = "दो लड़कों को मिली बदतमीजी करने की सजा! movie explained in hindi #short​ #movie​ #shorts​"

# Fixed Description
FIXED_DESCRIPTION = """दो लड़कों को मिली बदतमीजी करने की सजा! movie explained in hindi #short​ #movie​ #shorts​

📌 Disclaimer:
this videos here are made for the purposes of **Education, Review, Analysis, Research and Entertainment only. The video clips, images, audio or other content used in it is not intended to be a reproduction of the original work but rather a review and interpretation of it.

#moviereview​ #movie​ #movies​ #film​ #filmreview​ #cinema​ #moviereviews​ #review​ #films​ #cinephile​ #movienight​ #netflix​ #horror​ #movielover​ #movierecommendation​ #moviebuff​ #movietime​ #horrormovies​ #moviescenes​ #podcast​ #filmreviews​ #filmcritic​ #moviecritic​ #drama​ #movieaddict​ #thriller​ #comedy​ #moviereviewer​ #reviews​ #hollywood​ #cinematography​ #horrormovie​ #s​ #movielovers​ #moviepodcast​ #filmcommunity​ #moviecollection​ #moviequotes​ #cinephilecommunity​ #action​ #moviegeek​ #bluray​ #filmmaking​ #actor​ #bollywood​ #horrorfan​ #reviewfilm​ #bluraycollection​ #letterboxd​ #scifi​ #filmbuff​ #filmstagram​ #moviefan​ #horrorfilm​ #instamovies​ #cinematic​ #movieposter​ #disney​ #smovies​ #moviecollector​
"""

# Fixed Tags
FIXED_TAGS = [
    "Movie explanation in hindi", "movie review in Hindi", "Hollywood movie explain in hindi",
    "South movie explain in hindi", "horror movie explain", "sci  fi movie", "new movie",
    "best scene explain", "movies explained in hindi", "thriller movie", "explain",
    "Netflix", "Ott", "bigboss", "movie TV", "Bollywood movie explain",
    "movie hindi doubbed", "movie"
]

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

def upload_to_youtube(video_path):
    print("📤 Uploading video to YouTube Channel with fixed SEO...")
    creds = Credentials(
        token=None,
        refresh_token=YT_REFRESH_TOKEN.strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YT_CLIENT_ID.strip(),
        client_secret=YT_CLIENT_SECRET.strip()
    )
    youtube = build('youtube', 'v3', credentials=creds)
    
    body = {
        'snippet': {
            'title': FIXED_TITLE[:100], 
            'description': FIXED_DESCRIPTION, 
            'tags': FIXED_TAGS, 
            'categoryId': '24'
        },
        'status': {
            'privacyStatus': 'public', 
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    response = request.execute()
    print(f"🎉 SUCCESS! Video uploaded successfully. Video ID: {response.get('id')}")

def main():
    print("🚀 Starting automated upload system...")
    video_path, video_name = get_video_from_drive()
    if not video_path: return
    
    try: 
        upload_to_youtube(video_path)
    except Exception as e:
        print(f"❌ YouTube upload failed with error: {e}")
    finally:
        if os.path.exists(video_path): 
            os.remove(video_path)
            print("🧹 Temporary video file cleaned up.")

if __name__ == "__main__":
    main()
