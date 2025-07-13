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
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"텔레그램 전송 오류: {e}")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route("/ping")
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    triggered = []

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            df = df.dropna()

            if df.empty or len(df) < 15:
                print(f"❌ {ticker} 데이터 부족")
                continue

            close = df['Close']
            ma20 = close.rolling(window=20).mean()
            rsi = calculate_rsi(close)

            latest_close = close.iloc[-1]
            latest_ma20 = ma20.iloc[-1]
            latest_rsi = rsi.iloc[-1]

            if latest_rsi < 40 or latest_close > latest_ma20:
                triggered.append((ticker, latest_close, latest_rsi, latest_ma20))

        except Exception as e:
            print(f"❌ {ticker} 처리 중 에러: {e}")

    if triggered:
        alert = f"\n\n📡 조건 충족 종목 ({now})\n"
        for t, c, r, m in triggered:
            alert += f"✅ {t} | 종가: ${c:.2f} | RSI: {r:.2f} | MA20: {m:.2f}\n"
    else:
        alert = f"\n\n📡 조건 충족 종목 없음 ({now})"

    print(alert)
    send_telegram_alert(alert)
    return "pong"

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
