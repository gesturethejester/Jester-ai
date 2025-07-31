import os
import subprocess
import threading
import queue
import time
from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv
from utils import send_audio_to_replicate, get_chatgpt_response

load_dotenv()
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
buffer = queue.Queue()

TWITCH_USER = os.getenv("TWITCH_USER")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WAKE_WORD = "hey ges"

def listen_to_twitch_audio():
    os.makedirs("chunks", exist_ok=True)
    while True:
        print("[Streamlink] Checking if you're live...")
        cmd = f"streamlink --stdout https://twitch.tv/{TWITCH_USER} best | " \
              f"ffmpeg -loglevel quiet -i pipe:0 -f segment -segment_time 7 -c:a libmp3lame chunks/%03d.mp3"
        subprocess.run(cmd, shell=True)
        print("[Streamlink] Stream ended or failed. Retrying in 15s...")
        time.sleep(15)

def transcribe_loop():
    seen = set()
    while True:
        for fname in sorted(os.listdir("chunks")):
            if fname.endswith(".mp3") and fname not in seen:
                seen.add(fname)
                audio_path = f"chunks/{fname}"
                print(f"[Whisper] Sending {fname} to Replicate...")
                text = send_audio_to_replicate(audio_path, REPLICATE_API_TOKEN)
                print("[TRANSCRIBED]", text)
                if text and WAKE_WORD in text.lower():
                    prompt = text.lower().split(WAKE_WORD, 1)[-1].strip()
                    buffer.put(prompt)

def speak_loop():
    while True:
        msg = buffer.get()
        reply = get_chatgpt_response(msg)
        print("[RESPONSE]", reply)
        socketio.emit("overlay_text", {"text": reply})

@app.route("/")
def overlay():
    return render_template("overlay.html")

threading.Thread(target=listen_to_twitch_audio, daemon=True).start()
threading.Thread(target=transcribe_loop, daemon=True).start()
threading.Thread(target=speak_loop, daemon=True).start()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
