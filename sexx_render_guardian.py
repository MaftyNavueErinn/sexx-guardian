from pathlib import Path

code = """
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
    for ticker in WATCHLIST:
        try:
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            if df.empty:
                print(f"{ticker} 데이터 없음.")
                continue

            df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
            df["MA20"] = df["Close"].rolling(window=20).mean()
            df["MA60"] = df["Close"].rolling(window=60).mean()
            bb = ta.volatility.BollingerBands(close=df["Close"], window=20, window_dev=2)
            df["BB_upper"] = bb.bollinger_hband()
            df["BB_lower"] = bb.bollinger_lband()
            df["Volume_MA20"] = df["Volume"].rolling(window=20).mean()

            latest = df.iloc[-1]
            prev = df.iloc[-2]
            rsi = latest["RSI"]
            close = latest["Close"]
            ma20 = latest["MA20"]
            ma60 = latest["MA60"]
            bb_upper = latest["BB_upper"]
            bb_lower = latest["BB_lower"]
            volume = latest["Volume"]
            volume_ma = latest["Volume_MA20"]

            alert_msgs = []

            if rsi < 40:
                alert_msgs.append(f"⚠️ <b>{ticker}</b> RSI < 40 진입타점: RSI={rsi:.2f}, 종가={close:.2f}")

            if close > ma20 and prev["Close"] <= prev["MA20"]:
                alert_msgs.append(f"📈 <b>{ticker}</b> MA20 돌파: 종가={close:.2f} > MA20={ma20:.2f}")

            if close > ma60 and prev["Close"] <= prev["MA60"]:
                alert_msgs.append(f"📈 <b>{ticker}</b> MA60 돌파: 종가={close:.2f} > MA60={ma60:.2f}")

            if close <= bb_lower:
                alert_msgs.append(f"🔻 <b>{ticker}</b> 볼린저 하단 이탈: 종가={close:.2f}, BB 하단={bb_lower:.2f}")

            if volume > 1.5 * volume_ma:
                alert_msgs.append(f"💥 <b>{ticker}</b> 거래량 급등: 현재={volume:.0f}, 평균={volume_ma:.0f}")

            for msg in alert_msgs:
                send_telegram_message(msg)

        except Exception as e:
            print(f"{ticker} 에러 발생: {e}")

@app.route('/')
def home():
    return "Hello from Guardian"

@app.route('/ping')
def ping():
    check_alerts()
    return "pong"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
"""

file_path = "/mnt/data/sexx_render_guardian_modified.py"
Path(file_path).write_text(code)
file_path
