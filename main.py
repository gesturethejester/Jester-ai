import os
import requests
import time
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Twitch settings
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")  # just the name, not the full URL
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate .env values
if not all([TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_CHANNEL, OPENAI_API_KEY]):
    raise Exception("❌ Missing environment variables. Check your .env file.")

def get_oauth_token():
    print("🔑 Requesting Twitch OAuth token...")
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    token = response.json().get("access_token")
    print("✅ Twitch token obtained.")
    return token

def is_stream_live(token, username):
    print(f"📡 Checking if {username} is live...")
    url = f"https://api.twitch.tv/helix/streams?user_login={username}"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    live_data = response.json().get("data", [])
    if live_data:
        print("🟢 Stream is LIVE.")
    else:
        print("🔴 Stream is OFFLINE.")
    return bool(live_data)

@app.route("/", methods=["GET"])
def index():
    print("👋 Root endpoint hit.")
    return "✅ Jester AI is live and listening..."

@app.route("/trigger", methods=["POST"])
def trigger():
    print("🎯 Trigger endpoint called.")
    token = get_oauth_token()

    if not is_stream_live(token, TWITCH_CHANNEL):
        print("🚫 Stream offline. Aborting.")
        return {"error": "Stream is not live."}, 400

    print("🎧 Simulating audio stream capture...")
    time.sleep(1)

    print("🧠 Running dummy Whisper transcription...")
    time.sleep(1)
    transcript = "Show me your hi-hat, show me where your mind’s at."

    print(f"📝 Transcribed: {transcript}")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a funny, loyal jester sidekick named Marotte."},
            {"role": "user", "content": transcript}
        ]
    }

    print("🤖 Sending to OpenAI...")
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()["choices"][0]["message"]["content"]
    print(f"🎤 Marotte says: {result}")
    
    return {"response": result}

if __name__ == "__main__":
    print("🚀 Launching Flask app...")
    app.run(host="0.0.0.0", port=8080)
