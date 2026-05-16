import base64
import subprocess
import anthropic
from config.settings import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SCORE_PROMPT = """You are evaluating a video clip for a cute animals YouTube Shorts channel.

Look at this frame from the video and score it from 1 to 10 on:
1. Cuteness/emotional appeal (will viewers say "aww"?)
2. Hook strength (is something engaging happening that grabs attention immediately?)
3. Visual clarity (well-lit, in focus, not shaky?)

Respond with ONLY a JSON object like:
{"score": 8, "reason": "Fluffy kitten mid-yawn, very clear and endearing, strong immediate hook"}

Score 7+ means publish-worthy. Be honest and strict — only high-quality clips should pass."""


def extract_frame(video_path: str, second: float = 1.5) -> bytes:
    """Extract a single frame as JPEG bytes."""
    cmd = [
        "ffmpeg", "-ss", str(second), "-i", video_path,
        "-frames:v", "1", "-f", "image2", "-vcodec", "mjpeg", "pipe:1"
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.stdout


def score_clip(video_path: str) -> dict:
    """Score a clip using Claude Vision. Returns {score, reason}."""
    frame_bytes = extract_frame(video_path)
    if not frame_bytes:
        return {"score": 0, "reason": "could not extract frame"}

    frame_b64 = base64.standard_b64encode(frame_bytes).decode("utf-8")

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": frame_b64}},
                {"type": "text", "text": SCORE_PROMPT},
            ]
        }]
    )

    import json
    try:
        return json.loads(message.content[0].text)
    except Exception:
        return {"score": 0, "reason": "parse error"}
