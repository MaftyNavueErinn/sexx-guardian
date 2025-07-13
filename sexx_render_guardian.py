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

logging.basicConfig(level=logging.INFO)

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
        logging.error(f"텔레그램 에러: {e}")


def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


@app.route("/ping")
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"🔔 감시 시작됨: {now}")
    
    run_flag = request.args.get("run", default="0") == "1"

    alerts = []
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 20:
                continue

            close = df["Close"]
            rsi = calculate_rsi(close).iloc[-1]
            price = close.iloc[-1]
            ma20 = close.rolling(window=20).mean().iloc[-1]

            if rsi < 40 and price < ma20:
                alerts.append(f"<b>{ticker}</b> 📉 <b>사!!</b> (종가: ${price:.2f}, RSI: {rsi:.2f}, MA20: ${ma20:.2f})")
            elif rsi > 65 and price > ma20:
                alerts.append(f"<b>{ticker}</b> 🚨 <b>팔아!!</b> (종가: ${price:.2f}, RSI: {rsi:.2f}, MA20: ${ma20:.2f})")
        except Exception as e:
            logging.error(f"❌ {ticker} 처리 중 에러: {e}")

    if run_flag:
        if alerts:
            message = "\n".join(alerts)
        else:
            message = f"🔍 조건 충족 종목 없음. {now}"
        send_telegram_alert(message)

    return f"🔔 감시 시작됨: {now}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
