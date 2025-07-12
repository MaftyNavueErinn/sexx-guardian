import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask
from datetime import datetime
import logging
import requests

app = Flask(__name__)

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

RSI_THRESHOLD = 40

MAX_PAIN = {
    "TSLA": 310,
    "ORCL": 225,
    "MSFT": 490,
    "AMZN": 215,
    "NVDA": 160,
    "META": 700,
    "AAPL": 200,
    "AVGO": 265,
    "GOOGL": 177.5,
    "PSTG": 55,
    "SYM": 43,
    "TSM": 225,
    "ASML": 790,
    "AMD": 140,
    "ARM": 145
}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage"
    payload = {"chat_id": "<YOUR_CHAT_ID>", "text": text}
    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            print(f"❌ 텔레그램 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 텔레그램 전송 에러: {e}")

def get_rsi(close_prices, period=14):
    delta = close_prices.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_rsi_alerts():
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty:
                continue
            df.dropna(inplace=True)
            close = df["Close"]
            rsi = get_rsi(close).iloc[-1]
            price = close.iloc[-1]

            if rsi < RSI_THRESHOLD:
                msg = f"⚠️ [{ticker}] RSI 과매도 ({rsi:.2f}) 감지!\n현재가: ${price:.2f} / Max Pain: ${MAX_PAIN.get(ticker, 'N/A')}"
                send_telegram_message(msg)

        except Exception as e:
            print(f"❌ {ticker} 오류: {e}")

@app.route('/ping')
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    check_rsi_alerts()
    return f"[{now}] Ping OK - 감시 완료"

# Render용: gunicorn에서 실행되므로 app.run()은 제거
logging.basicConfig(level=logging.INFO)
