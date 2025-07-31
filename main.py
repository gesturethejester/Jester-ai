from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import requests
import time
import threading
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "gesturingthejester")
DEBUG_STATE = {
    "stream_live": False,
    "last_transcription": "",
    "last_error": ""
}

@app.route("/")
def index():
    return "Jester transcription server running"

@app.route("/debug")
def debug():
    return jsonify(DEBUG_STATE)

def is_stream_live():
    try:
        url = f"https://usher.ttvnw.net/api/channel/hls/{TWITCH_CHANNEL}.m3u8"
        r = requests.get(url)
        return "#EXTM3U" in r.text
    except Exception as e:
        DEBUG_STATE["last_error"] = f"is_stream_live error: {str(e)}"
        return False

def download_audio_loop():
    while True:
        print(f"Checking stream status for: {TWITCH_CHANNEL}")
        if is_stream_live():
            print("Stream is LIVE")
            DEBUG_STATE["stream_live"] = True
            try:
                # Simulated audio chunk (replace with real Whisper code)
                fake_text = "Test transcript from Whisper at " + time.strftime("%H:%M:%S")
                DEBUG_STATE["last_transcription"] = fake_text
                print("Transcribed:", fake_text)
                socketio.emit('transcription', {'text': fake_text})
            except Exception as e:
                err = f"Whisper error: {str(e)}"
                DEBUG_STATE["last_error"] = err
                print(err)
        else:
            DEBUG_STATE["stream_live"] = False
            print("Stream is OFFLINE")
        time.sleep(10)

@socketio.on("connect")
def on_connect():
    print("Overlay connected")

if __name__ == "__main__":
    threading.Thread(target=download_audio_loop, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=8080)
