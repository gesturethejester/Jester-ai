import os
import subprocess
import tempfile
import whisper
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import requests
import re
import time

load_dotenv()
TWITCH_USER = os.getenv("TWITCH_USER", "gesturethejester")
app = Flask(__name__)
socketio = SocketIO(app)

# Whisper model
model = whisper.load_model("tiny")

# Twitch API helpers
def get_access_token():
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    r = requests.post(url, params=params)
    return r.json().get("access_token")

def get_stream_url():
    token = get_access_token()
    headers = {
        "Client-ID": os.getenv("TWITCH_CLIENT_ID"),
        "Authorization": f"Bearer {token}"
    }
    url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_USER}"
    r = requests.get(url, headers=headers)
    if r.json().get("data"):
        m3u8 = f"https://usher.ttvnw.net/api/channel/hls/{TWITCH_USER}.m3u8"
        return m3u8
    return None

# Transcribe audio from m3u8
def transcribe_live():
    url = get_stream_url()
    if not url:
        print("Stream not live.")
        return

    print("Starting capture...")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        audio_file = tmp.name

    try:
        # Record 10 seconds from live stream
        subprocess.run([
            "ffmpeg", "-y",
            "-i", url,
            "-t", "10",
            "-vn",
            "-acodec", "libmp3lame",
            audio_file
        ], check=True)

        result = model.transcribe(audio_file)
        print(result["text"])
        return result["text"]

    except Exception as e:
        print("FFmpeg error:", e)
        return "Transcription failed"

@app.route("/")
def index():
    return "Jester transcription server running."

@app.route("/transcribe", methods=["GET"])
def transcribe_route():
    text = transcribe_live()
    return {"text": text or "No transcription available."}

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
