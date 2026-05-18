import os
import json
import subprocess
import anthropic
from config.settings import ANTHROPIC_API_KEY, COMPOSED_DIR
from pipeline.music import fetch_music_track

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client

CAPTION_PROMPT = """Write a short, punchy caption for a cute animal YouTube Short.
The video is: {description}

Rules:
- Max 6 words
- Conversational, warm, slightly funny
- No hashtags, no emojis
- End with a period or exclamation mark

Respond with ONLY the caption text."""

TITLE_PROMPT = """Write a YouTube title for a cute animal Short.
The video is: {description}

Rules:
- Max 60 characters
- Warm, curious, or slightly funny — makes people want to click
- No clickbait, no ALL CAPS, no emojis
- No hashtags

Respond with ONLY the title text."""

DESCRIPTION_PROMPT = """Write a YouTube description for a cute animal Short.
The video is: {description}

Rules:
- 2 sentences max, warm and conversational
- Then a blank line
- Then 5-8 relevant hashtags (e.g. #CuteAnimals #Fox #Shorts)
- Then a blank line
- Then exactly this line: 🤖 Generated with AI

Respond with ONLY the description text, no extra commentary."""


def generate_caption(description: str) -> str:
    message = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{"role": "user", "content": CAPTION_PROMPT.format(description=description)}]
    )
    return message.content[0].text.strip()


def generate_title(description: str) -> str:
    message = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=80,
        messages=[{"role": "user", "content": TITLE_PROMPT.format(description=description)}]
    )
    return message.content[0].text.strip()


def generate_description(description: str) -> str:
    message = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": DESCRIPTION_PROMPT.format(description=description)}]
    )
    return message.content[0].text.strip()


def has_audio_stream(video_path: str) -> bool:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        streams = json.loads(result.stdout).get("streams", [])
        return any(s.get("codec_type") == "audio" for s in streams)
    except Exception:
        return False


def compose_video(input_path: str, score_info: dict, output_name: str) -> tuple[str, str, str]:
    """Returns (output_path, title, youtube_description)."""
    reason = score_info.get("reason", "cute animal video")
    caption = generate_caption(reason)
    title = generate_title(reason)
    description = generate_description(reason)
    print(f"    Title: {title}")
    output_path = os.path.join(COMPOSED_DIR, f"{output_name}.mp4")

    # Strip any character that could break FFmpeg filter syntax
    safe_caption = caption
    for ch in ["'", '"', ":", "\\", "[", "]", "=", ";"]:
        safe_caption = safe_caption.replace(ch, " ")
    safe_caption = safe_caption.strip()
    print(f"    Caption: {safe_caption}")
    font_path = "C\\:/Windows/Fonts/arial.ttf"
    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"drawtext=fontfile='{font_path}':text='{safe_caption}':fontsize=44:fontcolor=white:"
        f"x=max(40\\, (w-text_w)/2):y=h-120:box=1:boxcolor=black@0.5:boxborderw=14"
    )

    music_path = fetch_music_track()
    video_has_audio = has_audio_stream(input_path)

    if music_path:
        print(f"    Adding background music: {os.path.basename(music_path)}")
        if video_has_audio:
            # Mix original audio + music at 25% volume
            audio_filter = (
                "[0:a]aresample=44100[va];"
                "[1:a]volume=0.25,aresample=44100[ma];"
                "[va][ma]amix=inputs=2:duration=first[aout]"
            )
            cmd = [
                "ffmpeg", "-i", input_path, "-i", music_path,
                "-vf", vf,
                "-filter_complex", audio_filter,
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k", "-t", "45", "-y", output_path
            ]
        else:
            # No source audio — use music only
            print("    Source has no audio, using music only.")
            cmd = [
                "ffmpeg", "-i", input_path, "-i", music_path,
                "-vf", vf,
                "-filter_complex", "[1:a]volume=0.25[aout]",
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k", "-t", "45", "-y", output_path
            ]
    else:
        print("    No music track available, composing without music.")
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-t", "45", "-y", output_path
        ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path, title, description
