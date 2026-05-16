"""
Poll YouTube metrics 24h and 72h after upload.
Results feed back into scoring calibration over time.
"""
import json
import os
from datetime import datetime, timezone
from pipeline.upload import get_youtube_client

METRICS_FILE = "data/metrics.json"


def load_metrics() -> dict:
    if not os.path.exists(METRICS_FILE):
        return {}
    with open(METRICS_FILE) as f:
        return json.load(f)


def save_metrics(data: dict):
    with open(METRICS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_upload(video_id: str, ai_score: int, filename: str):
    data = load_metrics()
    data[video_id] = {
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "ai_score": ai_score,
        "filename": filename,
        "polled_24h": False,
        "polled_72h": False,
        "stats": {}
    }
    save_metrics(data)


def poll_pending():
    """Check metrics for videos that haven't been polled yet."""
    youtube = get_youtube_client()
    data = load_metrics()
    now = datetime.now(timezone.utc)

    video_ids = [
        vid for vid, info in data.items()
        if not info["polled_24h"] or not info["polled_72h"]
    ]
    if not video_ids:
        return

    response = youtube.videos().list(
        part="statistics",
        id=",".join(video_ids)
    ).execute()

    for item in response.get("items", []):
        vid = item["id"]
        stats = item.get("statistics", {})
        uploaded_at = datetime.fromisoformat(data[vid]["uploaded_at"])
        hours_since = (now - uploaded_at).total_seconds() / 3600

        if hours_since >= 24 and not data[vid]["polled_24h"]:
            data[vid]["stats"]["24h"] = stats
            data[vid]["polled_24h"] = True

        if hours_since >= 72 and not data[vid]["polled_72h"]:
            data[vid]["stats"]["72h"] = stats
            data[vid]["polled_72h"] = True

    save_metrics(data)
    print(f"Polled metrics for {len(video_ids)} video(s)")
