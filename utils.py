import base64
import requests
import os

def send_audio_to_replicate(filepath, token):
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    json_data = {
        "version": "a0534528b8c6f7e3c0470c5c5ed4b64b31b395947d6dc6a44993edc003de2c9d",
        "input": {"audio": f"data:audio/mp3;base64,{b64}"}
    }

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.post("https://api.replicate.com/v1/predictions", json=json_data, headers=headers)
        return res.json()["prediction"]["transcription"]
    except Exception as e:
        print("[Replicate Error]", e)
        return None

def get_chatgpt_response(prompt):
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are Ges the Jester — a sharp, cheeky marotte puppet."},
            {"role": "user", "content": prompt}
        ]
    }
    res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
    return res.json()["choices"][0]["message"]["content"]
