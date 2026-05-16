"""
Main pipeline orchestrator. Run this once to kick off a full cycle:
fetch → filter → score → compose → (review) → upload
"""
import os
import shutil
from config.settings import (
    CANDIDATES_PER_RUN, MIN_QUALITY_SCORE, MANUAL_REVIEW,
    REJECTED_DIR, APPROVED_DIR, COMPOSED_DIR
)
from pipeline.fetch import fetch_candidates, download_clip
from pipeline.filter import passes_technical_filter
from pipeline.score import score_clip
from pipeline.compose import compose_video
from pipeline.upload import upload_short
from monitor.metrics import record_upload
import json

QUEUE_FILE = "data/review_queue.json"


def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE) as f:
        return json.load(f)


def save_queue(q):
    with open(QUEUE_FILE, "w") as f:
        json.dump(q, f, indent=2)


def run_pipeline():
    print("--- Fetching candidates ---")
    candidates = fetch_candidates(CANDIDATES_PER_RUN)
    print(f"Fetched {len(candidates)} candidates")

    scored = []

    for c in candidates:
        print(f"  Processing pexels_id={c['pexels_id']}...")

        # Download
        path = download_clip(c)

        # Technical filter
        passes, reason = passes_technical_filter(path)
        if not passes:
            print(f"    REJECTED (technical): {reason}")
            shutil.move(path, os.path.join(REJECTED_DIR, os.path.basename(path)))
            continue

        # AI quality score
        result = score_clip(path)
        score = result.get("score", 0)
        print(f"    AI score: {score}/10 — {result.get('reason','')}")

        if score < MIN_QUALITY_SCORE:
            print(f"    REJECTED (score too low)")
            shutil.move(path, os.path.join(REJECTED_DIR, os.path.basename(path)))
            continue

        scored.append({"candidate": c, "path": path, "score": score, "reason": result.get("reason", "")})

    if not scored:
        print("No clips passed quality filter this run.")
        return

    # Take top-scoring clip
    best = max(scored, key=lambda x: x["score"])
    print(f"\n--- Best clip: pexels_id={best['candidate']['pexels_id']} score={best['score']} ---")

    # Compose
    output_name = f"short_{best['candidate']['pexels_id']}"
    composed_path = compose_video(best["path"], {"reason": best["reason"]}, output_name)
    print(f"Composed: {composed_path}")

    if MANUAL_REVIEW:
        # Add to review queue
        queue = load_queue()
        queue.append({
            "filename": os.path.basename(composed_path),
            "score": best["score"],
            "reason": best["reason"],
            "status": "pending"
        })
        save_queue(queue)
        print("Added to review queue. Open http://localhost:5000 to approve.")
        return

    # Auto-upload if manual review is off
    _do_upload(composed_path, best)


def upload_approved():
    """Upload all approved videos from the review queue."""
    queue = load_queue()
    approved = [v for v in queue if v["status"] == "approve"]

    for item in approved:
        path = os.path.join(APPROVED_DIR, item["filename"])
        if not os.path.exists(path):
            continue
        _do_upload(path, item)
        item["status"] = "uploaded"

    save_queue(queue)


def _do_upload(path: str, info: dict):
    title = "You won't believe how cute this is 🐾"
    print(f"Uploading {path}...")
    video_id = upload_short(path, title=title)
    print(f"Uploaded! https://youtube.com/shorts/{video_id}")
    record_upload(video_id, info.get("score", 0), os.path.basename(path))
