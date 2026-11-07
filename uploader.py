
import os
import random
import sys
import json
import re
import yt_dlp

from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials


YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN")
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET")
GD_REFRESH_TOKEN = os.environ.get("GD_REFRESH_TOKEN")


# MAIN GOOGLE DRIVE FOLDER
MAIN_FOLDER_ID = "15iPb-a1NvZT9qcJnDUWFYSe1lZyYatJG"

# Duplicate upload tracking
UPLOADED_FILE = "uploaded_videos.json"


if not all([
    YT_REFRESH_TOKEN,
    YT_CLIENT_ID,
    YT_CLIENT_SECRET,
    GD_REFRESH_TOKEN
]):
    print("❌ Error: Missing required environment secrets!")
    sys.exit(1)


# VIDEO TITLE
FIXED_TITLE = "99% Of People Don't Know This Fact #shorts #viral"


# VIDEO DESCRIPTION
FIXED_DESCRIPTION = """99% Of People Don't Know This Fact #shorts #viral
"""


# ORIGINAL TAGS
FIXED_TAGS = [
    "AllahHuAkbar", "IslamicStatus", "IslamicReels", "IslamicShorts",
    "MuslimUmmah", "Allah", "Deen", "IslamicVibes", "Muslim",
    "ViralShorts", "TrendingShorts", "Shorts", "YouTubeShorts"
]


# ==========================================
# DUPLICATE UPLOAD PROTECTION
# ==========================================

def load_uploaded_videos():

    if os.path.exists(UPLOADED_FILE):
        try:
            with open(UPLOADED_FILE, "r") as f:
                return set(json.load(f))

        except Exception:
            print("⚠️ Could not read upload history!")
            sys.exit(1)

    return set()


def save_uploaded_video(video_id):

    uploaded = load_uploaded_videos()
    uploaded.add(video_id)

    with open(UPLOADED_FILE, "w") as f:
        json.dump(list(uploaded), f, indent=4)


def is_video_uploaded(video):

    app_properties = video.get("appProperties", {})

    if app_properties.get("youtubeUploaded") == "true":
        return True

    uploaded_ids = load_uploaded_videos()

    return video["id"] in uploaded_ids


def mark_video_uploaded(drive_service, video_id, youtube_id):

    # Get existing properties to avoid overwriting them
    file_info = drive_service.files().get(
        fileId=video_id,
        fields="appProperties",
        supportsAllDrives=True
    ).execute()

    properties = file_info.get("appProperties", {})

    properties.update({
        "youtubeUploaded": "true",
        "youtubeVideoId": str(youtube_id)
    })

    # Save upload history permanently in Google Drive
    drive_service.files().update(
        fileId=video_id,
        body={
            "appProperties": properties
        },
        supportsAllDrives=True
    ).execute()

    # Also maintain local JSON history
    save_uploaded_video(video_id)

    print("✅ Permanent duplicate protection saved!")


# ==========================================
# GOOGLE DRIVE FILE LISTING
# ==========================================

def list_drive_files(service, query):

    all_files = []
    page_token = None

    while True:

        results = service.files().list(
            q=query,
            fields="nextPageToken,files(id,name,mimeType,appProperties)",
            pageSize=1000,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        all_files.extend(results.get("files", []))

        page_token = results.get("nextPageToken")

        if not page_token:
            break

    return all_files


# ==========================================
# NATURAL BUNDLE ORDER
# ==========================================

def natural_sort_key(name):

    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", name)
    ]


# ==========================================
# GET VIDEO FROM GOOGLE DRIVE
# ==========================================

def get_video_from_drive():

    print("📥 Connecting to Google Drive...")

    creds = Credentials(
        token=None,
        refresh_token=GD_REFRESH_TOKEN.strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YT_CLIENT_ID.strip(),
        client_secret=YT_CLIENT_SECRET.strip()
    )

    drive_service = build(
        "drive",
        "v3",
        credentials=creds
    )

    # Find all bundle folders inside main folder
    folder_query = (
        f"'{MAIN_FOLDER_ID}' in parents "
        "and mimeType='application/vnd.google-apps.folder' "
        "and trashed=false"
    )

    folders = list_drive_files(
        drive_service,
        folder_query
    )

    # Sort bundles naturally: 1, 2, 3 ... 10
    folders.sort(
        key=lambda folder: natural_sort_key(folder["name"])
    )

    print(f"📂 Total bundles found: {len(folders)}")

    if not folders:

        print("❌ No bundle folders found!")
        print("Check MAIN_FOLDER_ID and Drive permissions.")

        return None, None, None, None

    # Process bundles one by one
    for folder in folders:

        bundle_id = folder["id"]
        bundle_name = folder["name"]

        print("\n================================")
        print(f"📁 CURRENT BUNDLE: {bundle_name}")
        print("================================")

        # Find videos inside current bundle
        video_query = (
            f"'{bundle_id}' in parents "
            "and mimeType contains 'video/' "
            "and trashed=false"
        )

        videos = list_drive_files(
            drive_service,
            video_query
        )

        # Filter already uploaded videos
        new_videos = [
            video for video in videos
            if not is_video_uploaded(video)
        ]

        print(f"🎬 Total videos: {len(videos)}")
        print(f"🆕 Remaining videos: {len(new_videos)}")

        # Current bundle completed?
        if not new_videos:

            print(f"✅ Bundle completed: {bundle_name}")
            print("➡️ Checking next bundle...")

            continue

        # Select one random video from current bundle
        selected_video = random.choice(new_videos)

        video_id = selected_video["id"]
        video_name = selected_video["name"]

        video_path = "temp_raw_video.mp4"

        print(f"🎯 Selected video: {video_name}")
        print(f"📥 Downloading from: {bundle_name}")

        request = drive_service.files().get_media(
            fileId=video_id,
            supportsAllDrives=True
        )

        with open(video_path, "wb") as f:
            f.write(request.execute())

        print("✅ Video downloaded successfully!")

        return (
            video_path,
            video_name,
            video_id,
            drive_service
        )

    print("\n🎉 ALL BUNDLES COMPLETED!")
    print("No new videos available for upload.")

    return None, None, None, None


# ==========================================
# SILENT TRENDING AUDIO PROCESSING
# ==========================================

def apply_silent_trending_audio(
    input_video_path,
    output_video_path
):

    print("🎵 Processing trending audio...")

    trending_song_title = ""
    trending_audio_file = "temp_trending_audio.mp3"

    ydl_opts_info = {
        "extract_flat": True,
        "playlistend": 1,
        "quiet": True
    }

    trending_url = (
        "https://www.youtube.com/feed/trending"
        "?bp=4gINGgt5dG1fYnJvd3Nl"
    )

    try:

        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:

            info = ydl.extract_info(
                trending_url,
                download=False
            )

            entries = info.get("entries", [])

            if entries:

                top_song = entries[0]

                first_video_url = (
                    top_song.get("url")
                    or f"https://www.youtube.com/watch?v={top_song.get('id')}"
                )

                trending_song_title = top_song.get(
                    "title",
                    "Trending Track"
                )

                print(
                    f"🔥 Found Trending Track: {trending_song_title}"
                )

                ydl_opts_dl = {
                    "format": "bestaudio/best",
                    "outtmpl": trending_audio_file,
                    "quiet": True
                }

                with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl_dl:

                    ydl_dl.download([first_video_url])

                if os.path.exists(trending_audio_file):

                    video = VideoFileClip(input_video_path)

                    trending_audio = AudioFileClip(
                        trending_audio_file
                    ).with_volume_scaling(0.0)

                    trending_audio = trending_audio.with_duration(
                        video.duration
                    )

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

                    trending_audio.close()
                    os.remove(trending_audio_file)

                    video.close()
                    final_video.close()

                    print(
                        "✅ Silent audio processing completed!"
                    )

                    return output_video_path, trending_song_title

    except Exception as e:

        print(
            f"⚠️ Trending audio process skipped: {e}"
        )

    return input_video_path, trending_song_title


# ==========================================
# YOUTUBE UPLOAD
# ==========================================

def upload_to_youtube(video_path, trending_song_name=""):

    print("📤 Uploading video to YouTube...")

    creds = Credentials(
        token=None,
        refresh_token=YT_REFRESH_TOKEN.strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YT_CLIENT_ID.strip(),
        client_secret=YT_CLIENT_SECRET.strip()
    )

    youtube = build(
        "youtube",
        "v3",
        credentials=creds
    )

    final_description = FIXED_DESCRIPTION
    final_tags = list(FIXED_TAGS)

    if trending_song_name:

        final_description += (
            f"\n--- Remix Audio Track: {trending_song_name} ---"
        )

        final_tags.append(trending_song_name[:20])

    body = {

        "snippet": {

            "title": FIXED_TITLE[:100],

            "description": final_description,

            "tags": final_tags,

            "categoryId": "24"
        },

        "status": {

            "privacyStatus": "public",

            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        video_path,
        chunksize=-1,
        resumable=True,
        mimetype="video/mp4"
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = request.execute()

    youtube_video_id = response.get("id")

    print(
        f"🎉 SUCCESS! YouTube Video ID: {youtube_video_id}"
    )

    return youtube_video_id


# ==========================================
# MAIN AUTOMATION SYSTEM
# ==========================================

def main():

    print("\n🚀 AUTOMATED YOUTUBE UPLOADER STARTED")

    raw_video_path = None
    final_video_path = "temp_final_video.mp4"

    try:

        (
            raw_video_path,
            video_name,
            drive_video_id,
            drive_service
        ) = get_video_from_drive()

        if not raw_video_path:
            return

        print(f"🎬 Processing: {video_name}")

        processed_video, trending_name = (
            apply_silent_trending_audio(
                raw_video_path,
                final_video_path
            )
        )

        # Upload to YouTube
        youtube_video_id = upload_to_youtube(
            processed_video,
            trending_song_name=trending_name
        )

        # Save duplicate history only after successful upload
        if youtube_video_id:

            mark_video_uploaded(
                drive_service,
                drive_video_id,
                youtube_video_id
            )

            print("✅ Video successfully uploaded and recorded!")

    except Exception as e:

        print(f"❌ Automation failed: {e}")

    finally:

        # Clean temporary files
        for temp_file in [
            raw_video_path,
            final_video_path,
            "temp_trending_audio.mp3"
        ]:

            if temp_file and os.path.exists(temp_file):

                try:
                    os.remove(temp_file)

                except Exception:
                    pass

        print("🧹 Temporary files cleaned up.")

        print("🏁 Automation run finished!")


if __name__ == "__main__":

    main()
