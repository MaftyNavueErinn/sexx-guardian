from pathlib import Path

# 기존에 문제가 됐던 코드
# Path(file_path).write_text(rsi_only_script)

# ✅ 수정본: 파일 저장 안 함 — Render에서는 불필요함
# 대신 기존 rsi_only_script 실행 로직만 유지

# 아래는 예시 구조로, 전체 context를 모르니 함수로 묶어서 구성
import os
import yfinance as yf
from ta.momentum import RSIIndicator
from flask import Flask
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ")
TELEGRAM_CHAT_ID = os.environ.get("7733010521")

TICKERS = ["TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

def send_telegram_alert(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("텔레그램 전송 오류:", e)

def check_rsi_and_alert():
    for ticker in TICKERS:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        if df.empty:
            continue
        close = df["Close"]
        rsi = RSIIndicator(close=close).rsi().iloc[-1]
        latest_price = close.iloc[-1]

        if rsi < 40:  # 널널하게 조건 설정
            msg = f"📉 {ticker} RSI 낮음 ({rsi:.2f}) — 현재가 ${latest_price:.2f}\n#매수타점?"
            send_telegram_alert(msg)

@app.route("/ping", methods=["GET"])
def ping():
    send_telegram_alert("🧪 테스트용 알림입니다. 시스템은 정상 작동 중입니다.")
    check_rsi_and_alert()
    return "알림 전송됨"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

