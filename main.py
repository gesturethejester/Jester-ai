import os
import subprocess
import threading
import queue
import whisper
import requests
import time
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
model = whisper.load_model("tiny")
wake_word = "hey ges"
buffer = queue.Queue()

TWITCH_USER = os.getenv("TWITCH_USER")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# ========== STREAM AUDIO ==========
def listen_to_twitch_audio():
    if not TWITCH_USER:
        print("Missing TWITCH_USER in .env")
        return

    os.makedirs("chunks", exist_ok=True)

    while True:
        print("[STREAMLINK] Checking for live stream...")
        cmd = f"streamlink --stdout https://twitch.tv/{TWITCH_USER} best | " \
              f"ffmpeg -loglevel quiet -i pipe:0 -f segment -segment_time 5 -c:a libmp3lame chunks/output%03d.mp3"

        process = subprocess.Popen(cmd, shell=True)
        process.wait()

        print("[STREAMLINK] Stream ended or not found. Retrying in 15s...")
        time.sleep(15)

# ========== TRANSCRIPTION ==========
def transcribe_audio_loop():
    seen = set()
    while True:
        for f in sorted(os.listdir("chunks")):
            if f.endswith(".mp3") and f not in seen:
                seen.add(f)
                result = model.transcribe(f"chunks/" + f)
                print("[TRANSCRIBED]", result['text'])
                if wake_word in result['text'].lower():
                    msg = result['text'].lower().split(wake_word, 1)[-1].strip()
                    buffer.put(msg)

# ========== CHATGPT ==========
def get_chatgpt_response(prompt):
    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are Ges the Jester, a sassy marotte puppet of the streamer. Respond playfully and wittily."},
            {"role": "user", "content": prompt}
        ]
    }
    res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
    return res.json()["choices"][0]["message"]["content"]

# ========== QUEUE TO OVERLAY ==========
def process_queue():
    while True:
        msg = buffer.get()
        reply = get_chatgpt_response(msg)
        print("[RESPONSE]", reply)
        socketio.emit('overlay_text', {'text': reply})

# ========== ROUTES ==========
@app.route("/")
def overlay():
    return render_template("overlay.html")

@app.route("/test", methods=["POST"])
def test_input():
    msg = request.form.get("msg", "")
    if msg:
        buffer.put(msg)
    return "OK"

# ========== THREADS ==========
threading.Thread(target=listen_to_twitch_audio, daemon=True).start()
threading.Thread(target=transcribe_audio_loop, daemon=True).start()
threading.Thread(target=process_queue, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=8080)
