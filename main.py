import os
import subprocess
import threading
import time
import openai
from flask import Flask, render_template, send_from_directory
from faster_whisper import WhisperModel

# CONFIGURATION
TWITCH_URL = "https://www.twitch.tv/GestureTheJester"
WAKE_PHRASE = "hey ges"
RESPONSE_PATH = "static/current_response.txt"
MODEL_SIZE = "tiny"

# Load OpenAI key from env var
openai.api_key = os.getenv("OPENAI_API_KEY")

# Start Flask server for overlay
app = Flask(__name__)

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

@app.route("/overlay.html")
def overlay():
    return render_template("overlay.html")

# Function to write and auto-clear the response
def update_response_file(response):
    with open(RESPONSE_PATH, "w", encoding="utf-8") as f:
        f.write(response)
    time.sleep(7)
    with open(RESPONSE_PATH, "w", encoding="utf-8") as f:
        f.write("")

# Transcription and ChatGPT logic
def listen_loop():
    print("Starting stream and transcription...")
    model = WhisperModel(MODEL_SIZE, compute_type="int8")
    process = subprocess.Popen(
        ["streamlink", "--stdout", TWITCH_URL, "audio_only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    segments, _ = model.transcribe(process.stdout, beam_size=1)
    for segment in segments:
        text = segment.text.strip().lower()
        print(f"[Heard]: {text}")
        if text.startswith(WAKE_PHRASE):
            prompt = text[len(WAKE_PHRASE):].strip()
            print(f"[Triggering GPT]: {prompt}")
            try:
                reply = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are the jester marotte voice of GestureTheJester. Be clever, weird, sharp."},
                        {"role": "user", "content": prompt}
                    ]
                ).choices[0].message.content.strip()
                print(f"[Reply]: {reply}")
                threading.Thread(target=update_response_file, args=(reply,)).start()
            except Exception as e:
                print(f"[ERROR]: {e}")

# Run everything
if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    with open(RESPONSE_PATH, "w") as f:
        f.write("")
    threading.Thread(target=listen_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=3000)
