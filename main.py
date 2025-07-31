import os
import time
import requests
import json
import openai
from flask import Flask, request, jsonify

# Debug toggle
DEBUG = True
def log(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

# Load env vars
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([TWITCH_CHANNEL, TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, OPENAI_API_KEY]):
    raise Exception("Missing environment variables. Check your .env file.")

openai.api_key = OPENAI_API_KEY
app = Flask(__name__)
twitch_oauth_token = None

def get_twitch_oauth():
    log("Requesting Twitch OAuth token...")
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    resp = requests.post(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    log("Received Twitch OAuth token.")
    return data["access_token"]

def is_stream_live():
    global twitch_oauth_token
    if not twitch_oauth_token:
        twitch_oauth_token = get_twitch_oauth()

    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {twitch_oauth_token}"
    }
    url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_CHANNEL}"
    log(f"Checking Twitch stream status for: {TWITCH_CHANNEL}")
    response = requests.get(url, headers=headers)
    data = response.json()
    live = bool(data.get("data"))
    log(f"Stream live: {live}")
    return live

@app.route("/", methods=["GET"])
def index():
    return "Twitch WhisperGPT backend is running."

@app.route("/trigger", methods=["POST"])
def trigger():
    payload = request.json
    user_text = payload.get("text", "")
    log(f"Received manual input: {user_text}")
    if not user_text:
        return jsonify({"error": "No text provided"}), 400

    try:
        log("Sending to OpenAI ChatGPT...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are the user's jester marotte—witty, bold, and always honest."},
                {"role": "user", "content": user_text}
            ]
        )
        reply = response.choices[0].message["content"]
        log(f"ChatGPT replied: {reply}")
        return jsonify({"reply": reply})
    except Exception as e:
        log(f"Error while generating ChatGPT reply: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    log("Starting Flask server...")
    app.run(host="0.0.0.0", port=8080)
