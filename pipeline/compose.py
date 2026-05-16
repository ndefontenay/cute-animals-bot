import os
import subprocess
import anthropic
from config.settings import ANTHROPIC_API_KEY, COMPOSED_DIR

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

CAPTION_PROMPT = """Write a short, punchy caption for a cute animal YouTube Short.
The video is: {description}

Rules:
- Max 8 words
- Conversational, warm, slightly funny
- No hashtags, no emojis
- End with a period or exclamation mark

Respond with ONLY the caption text."""


def generate_caption(description: str) -> str:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{"role": "user", "content": CAPTION_PROMPT.format(description=description)}]
    )
    return message.content[0].text.strip()


def compose_video(input_path: str, score_info: dict, output_name: str) -> str:
    """
    Crop to 9:16, burn in caption overlay, output to composed dir.
    Returns path to composed video.
    """
    caption = generate_caption(score_info.get("reason", "cute animal video"))
    output_path = os.path.join(COMPOSED_DIR, f"{output_name}.mp4")

    # FFmpeg filter: scale to 1080x1920 (9:16), add caption at bottom
    safe_caption = caption.replace("'", "\\'").replace(":", "\\:")
    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"drawtext=text='{safe_caption}':fontsize=52:fontcolor=white:"
        f"x=(w-text_w)/2:y=h-120:box=1:boxcolor=black@0.5:boxborderw=12"
    )

    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", "45",  # hard cap at 45s for Shorts
        "-y", output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path
