import subprocess
import json
from config.settings import VIDEO_MIN_DURATION, VIDEO_MAX_DURATION, VIDEO_MIN_HEIGHT


def probe(path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


def passes_technical_filter(path: str) -> tuple[bool, str]:
    """Returns (passes, reason_if_not)."""
    try:
        data = probe(path)
    except Exception as e:
        return False, f"ffprobe failed: {e}"

    video_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"), None
    )
    if not video_stream:
        return False, "no video stream"

    height = int(video_stream.get("height", 0))
    if height < VIDEO_MIN_HEIGHT:
        return False, f"resolution too low ({height}p)"

    duration = float(data.get("format", {}).get("duration", 0))
    if duration < VIDEO_MIN_DURATION:
        return False, f"too short ({duration:.1f}s)"
    if duration > VIDEO_MAX_DURATION:
        return False, f"too long ({duration:.1f}s)"

    return True, ""
