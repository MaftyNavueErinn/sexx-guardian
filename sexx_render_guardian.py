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
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[텔레그램 에러] {e}")


def calculate_rsi(close_prices, window=14):
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def check_signals():
    triggered = []
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty:
                raise ValueError("데이터가 비어 있음")

            close = df['Close']
            ma20 = close.rolling(window=20).mean()
            rsi = calculate_rsi(close)

            latest_close = float(close.iloc[-1])
            latest_ma20 = float(ma20.iloc[-1])
            latest_rsi = float(rsi.iloc[-1])

            if latest_rsi < 40 and latest_close > latest_ma20:
                triggered.append((ticker, latest_rsi, latest_close, latest_ma20))
        except Exception as e:
            send_telegram_alert(f"❌ {ticker} 처리 중 에러: {str(e)}")

    if triggered:
        for t, r, c, m in triggered:
            send_telegram_alert(f"✅ 진입 타점 감지: {t} | RSI={r:.2f}, 종가={c:.2f}, MA20={m:.2f}")
    else:
        send_telegram_alert(f"🔍 조건 충족 종목 없음. {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


@app.route("/ping")
def ping():
    if request.args.get("run") == "1":
        send_telegram_alert(f"🔔 감시 시작됨: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        check_signals()
    return "pong"


if __name__ == "__main__":
    app.run(debug=True, port=10000)
