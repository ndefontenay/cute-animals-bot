import os
import random

MUSIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "music"))
os.makedirs(MUSIC_DIR, exist_ok=True)


def fetch_music_track() -> str | None:
    """Pick a random track from data/music/. Returns path or None if folder is empty."""
    tracks = [
        os.path.join(MUSIC_DIR, f)
        for f in os.listdir(MUSIC_DIR)
        if f.lower().endswith((".mp3", ".wav", ".m4a"))
    ]
    if not tracks:
        print("    No music tracks found in data/music/ — composing without music.")
        return None
    return random.choice(tracks)
