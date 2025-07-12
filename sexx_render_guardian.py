from pathlib import Path

# Render 배포용 - /mnt/data 경로 제거하고 저장 기능 제거된 버전 생성
code = """
import requests
from flask import Flask, request

app = Flask(__name__)

TD_API = "5ccea133825e4496869229edbbfcc2a2"
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

@app.route("/")
def home():
    return "OK"

@app.route("/notify", methods=["POST"])
def notify():
    try:
        data = request.json
        message = data.get("message", "No message provided")
        send_telegram_message(message)
        return {"status": "sent"}, 200
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
"""

file_path = Path("/mnt/data/sexx_render_guardian.py")
file_path.write_text(code)
file_path.name
