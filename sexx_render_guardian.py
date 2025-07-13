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

MA_PERIOD = 20
RSI_PERIOD = 14
RSI_THRESHOLD = 40


def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"텔레그램 전송 오류: {e}")


def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(window=period).mean()
    ma_down = down.rolling(window=period).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi


def check_conditions(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        if df.empty or len(df) < MA_PERIOD:
            return None

        df = df.dropna()
        df["RSI"] = calculate_rsi(df["Close"], RSI_PERIOD)
        df["MA20"] = df["Close"].rolling(window=MA_PERIOD).mean()

        latest = df.iloc[-1]
        rsi = latest["RSI"]
        close = latest["Close"]
        ma20 = latest["MA20"]

        if pd.isna(rsi) or pd.isna(ma20):
            return None

        alert_messages = []
        if rsi < RSI_THRESHOLD:
            alert_messages.append(f"RSI {rsi:.2f} < {RSI_THRESHOLD}")
        if close > ma20:
            alert_messages.append(f"Close {close:.2f} > MA20 {ma20:.2f}")

        if alert_messages:
            return f"[{ticker}] " + ", ".join(alert_messages)
        return None
    except Exception as e:
        return f"❌ {ticker} 처리 중 에러: {e}"


@app.route("/ping")
def ping():
    run_flag = request.args.get("run")
    if run_flag != "1":
        return "pong"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alerts = [f"🔔 감시 시작됨: {timestamp}"]

    for ticker in TICKERS:
        result = check_conditions(ticker)
        if result:
            alerts.append(result)

    for msg in alerts:
        send_telegram_alert(msg)

    return "done"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
