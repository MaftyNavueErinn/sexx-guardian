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

headers = {
    "User-Agent": "Mozilla/5.0"
}

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        logging.error(f"텔레그램 전송 실패: {e}")

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def analyze_ticker(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            raise ValueError("데이터 부족")

        df["RSI"] = calculate_rsi(df["Close"])
        df["MA20"] = df["Close"].rolling(window=20).mean()

        latest = df.iloc[-1]
        rsi = latest["RSI"]
        close = latest["Close"]
        ma20 = latest["MA20"]

        # 경고 조건
        rsi_condition = rsi <= 40 if not pd.isna(rsi) else False
        ma_condition = close > ma20 if not pd.isna(close) and not pd.isna(ma20) else False

        if rsi_condition:
            send_telegram_alert(f"⚠️ <b>{ticker}</b> RSI={rsi:.2f} ➡️ 40 이하 진입 타점 가능성")
        if ma_condition:
            send_telegram_alert(f"✅ <b>{ticker}</b> 종가가 MA20({ma20:.2f}) 돌파함 ➡️ 추세 전환 가능")

    except Exception as e:
        send_telegram_alert(f"❌ {ticker} 처리 중 에러: {str(e)}")

@app.route("/ping")
def ping():
    run = request.args.get("run")
    if run == "1":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        send_telegram_alert(f"🔔 감시 시작됨: {now}")
        for ticker in TICKERS:
            analyze_ticker(ticker)
    return "pong"

if __name__ == "__main__":
    app.run(debug=True, port=10000)
