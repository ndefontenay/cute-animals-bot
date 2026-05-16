import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config.settings import YOUTUBE_SCOPES

TOKEN_FILE = "token.pickle"
CLIENT_SECRET_FILE = "client_secret.json"


def get_youtube_client():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, YOUTUBE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)


def upload_short(video_path: str, title: str, description: str = "", tags: list[str] = None) -> str:
    """Upload a video as a YouTube Short. Returns video ID."""
    youtube = get_youtube_client()

    body = {
        "snippet": {
            "title": title,
            "description": description + "\n\n#Shorts",
            "tags": (tags or []) + ["Shorts", "cute animals", "animals"],
            "categoryId": "15",  # Pets & Animals
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    return response["id"]
