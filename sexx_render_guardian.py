
import os
import yfinance as yf
import ta
import requests
from flask import Flask

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
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
            df["MA20"] = df["Close"].rolling(window=20).mean()
            latest = df.iloc[-1]
            rsi = latest["RSI"]
            close = latest["Close"]
            ma20 = latest["MA20"]

            if rsi < 35:
                send_telegram_message(f"🚨 {ticker} RSI < 35 진입타점: RSI={rsi:.2f}, 종가={close:.2f}, MA20={ma20:.2f}")

            if close > ma20 and df['Close'].iloc[-2] <= df['MA20'].iloc[-2]:
                send_telegram_message(f"🚨 {ticker} MA20 돌파 진입타점: 종가={close:.2f}, MA20={ma20:.2f}, RSI={rsi:.2f}")

        except Exception as e:
            print(f"{ticker} 에러 발생: {e}")

@app.route('/')
def home():
    return "Hello from Guardian"

@app.route('/ping')
def ping():
    check_alerts()
    return "pong"
