import logging
from flask import Flask, request
from twitch_audio_capture import TwitchAudioCapture

app = Flask(__name__)

# 🔧 Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

@app.route("/")
def index():
    logging.info("🏠 GET / - Server is running.")
    return "Jester transcription server running"

@app.route("/start", methods=["POST"])
def start_transcription():
    logging.info("📡 POST /start - Attempting to start Twitch audio capture.")

    try:
        username = request.json.get("username", "gesturethejester")
        model = request.json.get("model", "tiny")
        language = request.json.get("language", "en")

        logging.info(f"🎙️ Requested stream: {username}")
        logging.info(f"🧠 Whisper model: {model}, Language: {language}")

        capture = TwitchAudioCapture(username=username, model=model, language=language)
        capture.run()

        logging.info("✅ Transcription pipeline launched successfully.")
        return {"status": "Transcription started"}, 200

    except Exception as e:
        logging.error("❌ Error starting transcription", exc_info=True)
        return {"error": str(e)}, 500

if __name__ == "__main__":
    logging.info("🚀 Launching Jester AI Flask server...")
    app.run(host="0.0.0.0", port=8080)        print(f"Checking stream status for: {TWITCH_CHANNEL}")
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
