import os
import time
import threading
import requests
import subprocess
import tempfile
import openai
import whisper

from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Setup OpenAI
openai.api_key = OPENAI_API_KEY

# Load Whisper model
print("[DEBUG] Loading Whisper model (tiny)...")
model = whisper.load_model("tiny")

# Flask + SocketIO setup
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
is_listening = False


def get_access_token():
    print("[DEBUG] Requesting Twitch access token...")
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    res = requests.post(url, params=params).json()
    return res.get("access_token")


def check_if_stream_live():
    token = get_access_token()
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": "Bearer " + token
    }
    url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_CHANNEL}"
    res = requests.get(url, headers=headers).json()
    return bool(res.get("data"))


def run_chatgpt(prompt):
    try:
        print("[DEBUG] Sending prompt to ChatGPT: " + prompt)
        messages = [
            {"role": "system", "content": "You are a jester puppet version of the user. Be weird, witty, and insightful."},
            {"role": "user", "content": prompt}
        ]
        res = openai.ChatCompletion.create(model="gpt-4", messages=messages)
        return res.choices[0].message.content.strip()
    except Exception as e:
        print("[ERROR] ChatGPT failed: " + str(e))
        return "Oops. I forgot my punchline."


def transcribe_audio_and_respond(file_path):
    try:
        print("[WHISPER] Transcribing audio...")
        result = model.transcribe(file_path)
        text = result["text"].strip()
        print("[WHISPER] Text: " + text)

        if "hey ges" in text.lower():
            prompt = text.split("hey ges", 1)[-1].strip()
            if not prompt:
                prompt = "Just say something."
            response = run_chatgpt(prompt)
            socketio.emit("overlay_response", response)
        else:
            print("[WHISPER] Wake word not found.")

    except Exception as e:
        print("[ERROR] Transcription failed: " + str(e))


def stream_audio():
    global is_listening
    is_listening = True
    print("[AUDIO] Capturing audio...")

    with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_audio:
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", f"https://www.twitch.tv/{TWITCH_CHANNEL}",
            "-t", "10",
            "-vn", "-acodec", "libmp3lame",
            temp_audio.name
        ]
        try:
            subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[AUDIO] Audio file captured: " + temp_audio.name)
            transcribe_audio_and_respond(temp_audio.name)
        except Exception as e:
            print("[ERROR] Failed to stream audio: " + str(e))

    is_listening = False


def monitor_stream():
    global is_listening
    while True:
        try:
            live = check_if_stream_live()
            if live:
                print("[STATUS] Twitch stream is LIVE")
                socketio.emit("overlay_log", "[STATUS] Stream LIVE. Listening...")
                if not is_listening:
                    threading.Thread(target=stream_audio).start()
            else:
                print("[STATUS] Twitch stream is OFFLINE")
                socketio.emit("overlay_log", "[STATUS] Stream is OFFLINE.")
        except Exception as e:
            print("[ERROR] Stream check failed: " + str(e))
        time.sleep(15)


@app.route("/")
def index():
    return render_template("overlay.html")


if __name__ == "__main__":
    print("[SERVER] Starting server on port 8080")
    socketio.start_background_task(target=monitor_stream)
    socketio.run(app, host="0.0.0.0", port=8080, debug=True)
