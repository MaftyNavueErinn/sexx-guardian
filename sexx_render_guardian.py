import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, request
from datetime import datetime
import logging
import requests

app = Flask(__name__)

TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": message}
    requests.post(url, data=data)

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route("/ping")
def ping():
    run_param = request.args.get("run")
    if run_param != "1":
        return "pong"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.warning(f"🔔 감시 시작됨: {now}")
    send_telegram_alert(f"🔔 감시 시작됨: {now}")

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 15:
                send_telegram_alert(f"❌ {ticker} 데이터 부족")
                continue

            df["RSI"] = calculate_rsi(df["Close"])
            df["MA20"] = df["Close"].rolling(window=20).mean()

            rsi = df["RSI"].iloc[-1]
            close = df["Close"].iloc[-1]
            ma20 = df["MA20"].iloc[-1]

            if pd.isna(rsi) or pd.isna(close) or pd.isna(ma20):
                send_telegram_alert(f"⚠️ {ticker} 계산값 누락(RSI 또는 MA20)")
                continue

            if rsi < 40:
                send_telegram_alert(f"📉 {ticker} RSI 과매도 감지: RSI={rsi:.2f}")
            elif close > ma20:
                send_telegram_alert(f"🚀 {ticker} MA20 돌파: Close={close:.2f} > MA20={ma20:.2f}")
        
        except Exception as e:
            send_telegram_alert(f"❌ {ticker} 처리 중 에러: {str(e)}")

    return "done"
