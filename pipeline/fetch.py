import os
import json
import random
import requests
from config.settings import PEXELS_API_KEY, CANDIDATES_DIR, PEXELS_QUERIES, CANDIDATES_PER_RUN

SEEN_IDS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "seen_ids.json"))


def load_seen_ids() -> set:
    if not os.path.exists(SEEN_IDS_FILE):
        return set()
    with open(SEEN_IDS_FILE) as f:
        return set(json.load(f))


def save_seen_id(pexels_id: int):
    seen = load_seen_ids()
    seen.add(pexels_id)
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(seen), f)


def fetch_candidates(n: int = CANDIDATES_PER_RUN) -> list[dict]:
    """Fetch n candidate video clips from Pexels, skipping already-seen IDs."""
    seen = load_seen_ids()
    query = random.choice(PEXELS_QUERIES)
    headers = {"Authorization": PEXELS_API_KEY}

    candidates = []
    page = 1
    while len(candidates) < n and page <= 5:
        params = {"query": query, "per_page": n, "orientation": "portrait", "page": page}
        resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
        resp.raise_for_status()
        videos = resp.json().get("videos", [])
        if not videos:
            break

        for v in videos:
            if v["id"] in seen:
                continue

            files = sorted(v.get("video_files", []), key=lambda f: f.get("height", 0), reverse=True)
            portrait_files = [f for f in files if f.get("width", 0) < f.get("height", 1)]
            if not portrait_files:
                portrait_files = files

            best = portrait_files[0] if portrait_files else None
            if not best:
                continue

            candidates.append({
                "pexels_id": v["id"],
                "url": best["link"],
                "width": best.get("width"),
                "height": best.get("height"),
                "duration": v.get("duration"),
                "query": query,
                "photographer": v.get("user", {}).get("name", ""),
            })

            if len(candidates) >= n:
                break

        page += 1

    skipped = len(seen)
    if skipped:
        print(f"  (Skipped {skipped} already-seen clip IDs)")

    return candidates


def download_clip(candidate: dict) -> str:
    """Download a clip to the candidates dir. Returns local file path."""
    path = os.path.join(CANDIDATES_DIR, f"{candidate['pexels_id']}.mp4")
    if os.path.exists(path):
        return path

    resp = requests.get(candidate["url"], stream=True)
    resp.raise_for_status()
    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return path
