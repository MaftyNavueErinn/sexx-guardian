from pathlib import Path

# 전체 코드 문자열
rsi_only_script = '''
import os
import yfinance as yf
import ta
import requests
from flask import Flask

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
WATCHLIST = ["TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("텔레그램 전송 오류:", e)

def check_alerts():
    send_telegram_message("🧪 테스트용 알림입니다. 시스템은 정상 작동 중입니다.")
    for ticker in WATCHLIST:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty:
                print(f"{ticker} 데이터 없음.")
                continue

            df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
            latest = df.iloc[-1]
            rsi = latest["RSI"]
            close = latest["Close"]

            if rsi < 60:
                send_telegram_message(f"📉 <b>{ticker}</b> RSI 진입타점 감지!\nRSI: {rsi:.2f} / 종가: ${close:.2f}")

        except Exception as e:
            print(f"{ticker} 에러 발생: {e}")

@app.route('/')
def home():
    return "Hello from RSI Guardian"

@app.route('/ping')
def ping():
    check_alerts()
    return "pong"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
'''

# 파일 저장
file_path = "/mnt/data/sexx_render_guardian_rsi_only.py"
Path(file_path).write_text(rsi_only_script)

file_path
