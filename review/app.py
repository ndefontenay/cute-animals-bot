"""
Lightweight local review queue — runs on http://localhost:5000
Shows composed videos one at a time for approve/reject before upload.
"""
import os
import json
import shutil
from flask import Flask, send_file, jsonify, request, redirect
from config.settings import COMPOSED_DIR, APPROVED_DIR, REJECTED_DIR

app = Flask(__name__)
QUEUE_FILE = "data/review_queue.json"


def load_queue() -> list:
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE) as f:
        return json.load(f)


def save_queue(q: list):
    with open(QUEUE_FILE, "w") as f:
        json.dump(q, f, indent=2)


@app.get("/")
def index():
    queue = load_queue()
    pending = [v for v in queue if v["status"] == "pending"]
    if not pending:
        return "<h2>No videos pending review.</h2>"

    item = pending[0]
    return f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:40px auto;text-align:center">
      <h2>Review Queue ({len(pending)} pending)</h2>
      <video src="/video/{item['filename']}" controls autoplay muted
             style="width:300px;border-radius:12px"></video>
      <p><b>{item['filename']}</b></p>
      <p style="color:#666">{item.get('reason','')}</p>
      <p>AI score: <b>{item.get('score','?')}/10</b></p>
      <form method="POST" action="/review">
        <input type="hidden" name="filename" value="{item['filename']}">
        <button name="action" value="approve"
                style="background:#22c55e;color:white;padding:12px 32px;
                       font-size:18px;border:none;border-radius:8px;cursor:pointer;margin:8px">
          Approve
        </button>
        <button name="action" value="reject"
                style="background:#ef4444;color:white;padding:12px 32px;
                       font-size:18px;border:none;border-radius:8px;cursor:pointer;margin:8px">
          Reject
        </button>
      </form>
    </body></html>
    """


@app.get("/video/<filename>")
def serve_video(filename):
    path = os.path.join(COMPOSED_DIR, filename)
    return send_file(path, mimetype="video/mp4")


@app.post("/review")
def review():
    filename = request.form["filename"]
    action = request.form["action"]
    src = os.path.join(COMPOSED_DIR, filename)

    queue = load_queue()
    for item in queue:
        if item["filename"] == filename:
            item["status"] = action
            break
    save_queue(queue)

    dest_dir = APPROVED_DIR if action == "approve" else REJECTED_DIR
    shutil.move(src, os.path.join(dest_dir, filename))

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
