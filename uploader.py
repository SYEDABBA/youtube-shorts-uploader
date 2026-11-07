
import os
import random
import sys
import json
import yt_dlp
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN")
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET")
GD_REFRESH_TOKEN = os.environ.get("GD_REFRESH_TOKEN")

# New Google Drive folder
FOLDER_IDS = ["15iPb-a1NvZT9qcJnDUWFYSe1lZyYatJG"]

# Duplicate upload tracking
UPLOADED_FILE = "uploaded_videos.json"

if not all([YT_REFRESH_TOKEN, YT_CLIENT_ID, YT_CLIENT_SECRET, GD_REFRESH_TOKEN]):
    print("❌ Error: Missing required environment secrets!")
    sys.exit(1)

# New Title
FIXED_TITLE = "99% Of People Don't Know This Fact #shorts #viral"

# New Description
FIXED_DESCRIPTION = """99% Of People Don't Know This Fact #shorts #viral
"""

# Original Tags (unchanged)
FIXED_TAGS = [
    "AllahHuAkbar", "IslamicStatus", "IslamicReels", "IslamicShorts",
    "MuslimUmmah", "Allah", "Deen", "IslamicVibes", "Muslim",
    "ViralShorts", "TrendingShorts", "Shorts", "YouTubeShorts"
]


# Load previously uploaded video IDs
def load_uploaded_videos():
    if os.path.exists(UPLOADED_FILE):
        try:
            with open(UPLOADED_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            print("⚠️ Could not read upload history!")
            sys.exit(1)
    return set()


# Save uploaded video IDs
def save_uploaded_video(video_id):
    uploaded = load_uploaded_videos()
    uploaded.add(video_id)

    with open(UPLOADED_FILE, "w") as f:
        json.dump(list(uploaded), f, indent=4)


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

    results = drive_service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()

    items = results.get('files', [])

    # Remove previously uploaded videos
    uploaded_ids = load_uploaded_videos()

    new_videos = [
        video for video in items
        if video['id'] not in uploaded_ids
    ]

    if not new_videos:
        print("✅ No new videos available. All videos already uploaded!")
        return None, None, None

    random_video = random.choice(new_videos)

    video_id = random_video['id']
    video_name = random_video['name']

    video_path = "temp_raw_video.mp4"

    print(f"✅ New video found: {video_name}. Downloading...")

    request = drive_service.files().get_media(fileId=video_id)

    with open(video_path, "wb") as f:
        f.write(request.execute())

    return video_path, video_name, video_id


def apply_silent_trending_audio(input_video_path, output_video_path):
    print("🎵 Hijacking YouTube Trending Music for Algorithm Boost...")

    trending_song_title = ""
    trending_audio_file = "temp_trending_audio.mp3"

    ydl_opts_info = {
        'extract_flat': True,
        'playlistend': 1,
        'quiet': True
    }

    trending_url = "https://www.youtube.com/feed/trending?bp=4gINGgt5dG1fYnJvd3Nl"

    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(trending_url, download=False)

            entries = info.get('entries', [])

            if entries:
                top_song = entries[0]

                first_video_url = top_song.get('url') or f"https://www.youtube.com/watch?v={top_song.get('id')}"

                trending_song_title = top_song.get('title', 'Trending Track')

                print(f"🔥 Found Trending Track: {trending_song_title}")

                ydl_opts_dl = {
                    'format': 'bestaudio/best',
                    'outtmpl': trending_audio_file,
                    'quiet': True
                }

                with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl_dl:
                    ydl_dl.download([first_video_url])

                if os.path.exists(trending_audio_file):

                    video = VideoFileClip(input_video_path)

                    trending_audio = AudioFileClip(
                        trending_audio_file
                    ).with_volume_scaling(0.0)

                    trending_audio = trending_audio.with_duration(video.duration)

                    if video.audio:
                        final_audio = CompositeAudioClip([
                            video.audio,
                            trending_audio
                        ])
                    else:
                        final_audio = trending_audio

                    final_video = video.with_audio(final_audio)

                    final_video.write_videofile(
                        output_video_path,
                        codec="libx264",
                        audio_codec="aac",
                        logger=None
                    )

                    os.remove(trending_audio_file)

                    video.close()
                    final_video.close()

                    print("✅ Silent Trending Audio successfully blended with original video!")

                    return output_video_path, trending_song_title

    except Exception as e:
        print(f"⚠️ Trending audio process skipped due to error: {e}")

    return input_video_path, trending_song_title


def upload_to_youtube(video_path, trending_song_name=""):
    print("📤 Uploading video to YouTube Channel...")

    creds = Credentials(
        token=None,
        refresh_token=YT_REFRESH_TOKEN.strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YT_CLIENT_ID.strip(),
        client_secret=YT_CLIENT_SECRET.strip()
    )

    youtube = build('youtube', 'v3', credentials=creds)

    final_description = FIXED_DESCRIPTION
    final_tags = list(FIXED_TAGS)

    if trending_song_name:
        final_description += f"\n--- Remix Audio Track: {trending_song_name} ---"
        final_tags.append(trending_song_name[:20])

    body = {
        'snippet': {
            'title': FIXED_TITLE[:100],
            'description': final_description,
            'tags': final_tags,
            'categoryId': '24'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(
        video_path,
        chunksize=-1,
        resumable=True,
        mimetype='video/mp4'
    )

    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = request.execute()

    print(f"🎉 SUCCESS! Video uploaded successfully. Video ID: {response.get('id')}")

    return response.get('id')


def main():
    print("🚀 Starting automated upload system...")

    raw_video_path, video_name, drive_video_id = get_video_from_drive()

    if not raw_video_path:
        return

    final_video_path = "temp_final_video.mp4"

    try:
        processed_video, trending_name = apply_silent_trending_audio(
            raw_video_path,
            final_video_path
        )

        youtube_video_id = upload_to_youtube(
            processed_video,
            trending_song_name=trending_name
        )

        # Save only after successful YouTube upload
        if youtube_video_id:
            save_uploaded_video(drive_video_id)
            print("✅ Video ID saved. Duplicate upload protection activated!")

    except Exception as e:
        print(f"❌ YouTube upload failed with error: {e}")

    finally:
        for temp_file in [raw_video_path, final_video_path]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

        print("🧹 Temporary video files cleaned up.")


if __name__ == "__main__":
    main()
