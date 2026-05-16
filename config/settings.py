import os
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

POSTING_HOUR = int(os.getenv("POSTING_HOUR", 8))
CANDIDATES_PER_RUN = int(os.getenv("CANDIDATES_PER_RUN", 20))
MIN_QUALITY_SCORE = int(os.getenv("MIN_QUALITY_SCORE", 7))
MANUAL_REVIEW = os.getenv("MANUAL_REVIEW", "true").lower() == "true"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CANDIDATES_DIR = os.path.join(DATA_DIR, "candidates")
COMPOSED_DIR = os.path.join(DATA_DIR, "composed")
REJECTED_DIR = os.path.join(DATA_DIR, "rejected")
APPROVED_DIR = os.path.join(DATA_DIR, "approved")

PEXELS_QUERIES = [
    "cute cat", "cute dog", "baby animal", "funny kitten",
    "puppy playing", "cute bunny", "baby duck", "hamster",
]

VIDEO_MIN_DURATION = 8    # seconds
VIDEO_MAX_DURATION = 45   # seconds
VIDEO_MIN_HEIGHT = 720    # pixels
