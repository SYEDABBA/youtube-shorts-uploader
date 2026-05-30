import os
import json
import random
import logging
import io
from groq import Groq
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fetch credentials from environment variables
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
YT_CLIENT_ID = os.environ.get('YT_CLIENT_ID')
YT_CLIENT_SECRET = os.environ.get('YT_CLIENT_SECRET')
YT_REFRESH_TOKEN = os.environ.get('YT_REFRESH_TOKEN')
GD_REFRESH_TOKEN = os.environ.get('GD_REFRESH_TOKEN')

# Google Drive folder IDs - Your actual folder IDs
FOLDER_IDS = [
    "16F9CmM4abxAvX_nUPyAKXSSl94T0xUMV",
    "1dVjqB7m_IKHIZ2-PN8PmNiXhC4jRVFbU"
]

# Constants
SUPPORTED_FORMATS = ['.mp4', '.mkv']
TEMP_VIDEO_PATH = 'temp_video.mp4'
GROQ_MODEL = 'llama3-8b-8192'


def get_drive_service():
    """Initialize and return Google Drive service with refresh token."""
    try:
        credentials = Credentials(
            token=None,
            refresh_token=GD_REFRESH_TOKEN,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=YT_CLIENT_ID,
            client_secret=YT_CLIENT_SECRET
        )
        credentials.refresh(Request())
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        logger.error(f"Error creating Drive service: {str(e)}")
        return None


def get_youtube_service():
    """Initialize and return YouTube service with refresh token."""
    try:
        credentials = Credentials(
            token=None,
            refresh_token=YT_REFRESH_TOKEN,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=YT_CLIENT_ID,
            client_secret=YT_CLIENT_SECRET
        )
        credentials.refresh(Request())
        return build('youtube', 'v3', credentials=credentials)
    except Exception as e:
        logger.error(f"Error creating YouTube service: {str(e)}")
        return None


def get_video_from_drive():
    """
    Pick a random folder from FOLDER_IDS, find a random video file,
    download it, and save as temp_video.mp4.
    """
    try:
        logger.info("Starting video download from Google Drive...")
        
        # Select random folder
        folder_id = random.choice(FOLDER_IDS)
        logger.info(f"Selected folder: {folder_id}")
        
        # Initialize Drive service
        drive_service = get_drive_service()
        if not drive_service:
            logger.error("Failed to initialize Drive service")
            return None
        
        # Find all video files in the folder
        query = f"'{folder_id}' in parents and trashed=false and ("
        query += " or ".join([f"mimeType='video/{fmt.strip('.')}'" for fmt in SUPPORTED_FORMATS])
        query += ")"
        
        logger.info(f"Searching for videos with query: {query}")
        
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, size)',
            pageSize=100
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            logger.error(f"No video files found in folder {folder_id}")
            return None
        
        logger.info(f"Found {len(files)} video(s) in the folder")
        
        # Select random video file
        video_file = random.choice(files)
        logger.info(f"Selected video: {video_file['name']} (Size: {video_file.get('size', 'unknown')} bytes)")
        
        # Download the file
        try:
            request = drive_service.files().get_media(fileId=video_file['id'])
            file_content = request.execute()
            
            with open(TEMP_VIDEO_PATH, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"Successfully downloaded {video_file['name']} to {TEMP_VIDEO_PATH}")
            return video_file['name']
        except Exception as e:
            logger.error(f"Failed to download video file: {str(e)}")
            return None
                
    except Exception as e:
        logger.error(f"Error downloading video from Drive: {str(e)}")
        return None


def generate_seo(video_name):
    """
    Use Groq API to generate YouTube Title, Description, and Tags
    based on the video file name.
    """
    try:
        logger.info(f"Generating SEO content for: {video_name}")
        
        # Initialize Groq client
        client = Groq(api_key=GROQ_API_KEY)
        
        # Create prompt
        prompt = f"""Based on the video filename: "{video_name}", generate YouTube Shorts SEO content.

Please provide a response in the following JSON format:
{{
    "title": "A catchy YouTube Shorts title with #shorts hashtag (max 60 chars)",
    "description": "An engaging YouTube description (2-3 sentences with relevant keywords)",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Generate content that is:
- Catchy and engaging for YouTube Shorts
- Optimized for discoverability
- Includes relevant hashtags
- Professional and appropriate

Respond ONLY with valid JSON, no additional text."""

        # Call Groq API
        logger.info("Calling Groq API for SEO generation...")
        message = client.messages.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse response
        response_text = message.content[0].text
        logger.info(f"Groq response received: {response_text[:100]}...")
        
        # Extract JSON from response
        seo_data = json.loads(response_text)
        
        logger.info("SEO content generated successfully")
        logger.info(f"Title: {seo_data.get('title')}")
        logger.info(f"Description: {seo_data.get('description')}")
        logger.info(f"Tags: {seo_data.get('tags')}")
        
        return seo_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Groq response as JSON: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error generating SEO content: {str(e)}")
        return None


def upload_to_youtube(video_path, seo_data):
    """
    Upload video to YouTube as a public Shorts video using the YouTube Data API v3.
    """
    try:
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        file_size = os.path.getsize(video_path)
        logger.info(f"Uploading video to YouTube: {video_path} (Size: {file_size} bytes)")
        
        # Initialize YouTube service
        youtube = get_youtube_service()
        if not youtube:
            logger.error("Failed to initialize YouTube service")
            return False
        
        # Prepare video metadata
        body = {
            'snippet': {
                'title': seo_data['title'],
                'description': seo_data['description'],
                'tags': seo_data['tags'],
                'categoryId': '23'  # Entertainment category
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        logger.info(f"Video metadata prepared: {json.dumps(body, indent=2)}")
        
        # Upload video
        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )
        
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        logger.info("Starting YouTube upload...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Upload progress: {int(status.progress() * 100)}%")
        
        video_id = response.get('id')
        logger.info(f"✅ Video uploaded successfully! Video ID: {video_id}")
        logger.info(f"Watch at: https://www.youtube.com/watch?v={video_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error uploading to YouTube: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def cleanup():
    """Remove temporary video file."""
    try:
        if os.path.exists(TEMP_VIDEO_PATH):
            os.remove(TEMP_VIDEO_PATH)
            logger.info(f"✅ Cleaned up temporary file: {TEMP_VIDEO_PATH}")
    except Exception as e:
        logger.error(f"Error cleaning up temporary file: {str(e)}")


def main():
    """Main function to orchestrate the upload process."""
    logger.info("=" * 60)
    logger.info("Starting YouTube Shorts Uploader...")
    logger.info("=" * 60)
    
    try:
        # Validate environment variables
        required_vars = {
            'GROQ_API_KEY': GROQ_API_KEY,
            'YT_CLIENT_ID': YT_CLIENT_ID,
            'YT_CLIENT_SECRET': YT_CLIENT_SECRET,
            'YT_REFRESH_TOKEN': YT_REFRESH_TOKEN,
            'GD_REFRESH_TOKEN': GD_REFRESH_TOKEN
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        logger.info("✅ All environment variables loaded successfully")
        logger.info(f"📁 Configured folders: {len(FOLDER_IDS)}")
        
        # Download video from Google Drive
        logger.info("\n[Step 1/4] Downloading video from Google Drive...")
        video_name = get_video_from_drive()
        if not video_name:
            logger.error("❌ Failed to download video from Google Drive")
            return False
        
        logger.info(f"✅ Video downloaded: {video_name}\n")
        
        # Generate SEO content
        logger.info("[Step 2/4] Generating SEO content with Groq AI...")
        seo_data = generate_seo(video_name)
        if not seo_data:
            logger.error("❌ Failed to generate SEO content")
            cleanup()
            return False
        
        logger.info("✅ SEO content generated\n")
        
        # Upload to YouTube
        logger.info("[Step 3/4] Uploading to YouTube...")
        success = upload_to_youtube(TEMP_VIDEO_PATH, seo_data)
        
        # Cleanup
        logger.info("\n[Step 4/4] Cleaning up...")
        cleanup()
        
        logger.info("=" * 60)
        if success:
            logger.info("✅ YouTube Shorts upload completed successfully!")
            logger.info("=" * 60)
            return True
        else:
            logger.error("❌ Failed to upload video to YouTube")
            logger.info("=" * 60)
            return False
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in main function: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        cleanup()
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
