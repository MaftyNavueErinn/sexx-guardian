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
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return pd.Series(rsi, index=close.index)

@app.route("/ping")
def ping():
    run_param = request.args.get("run")
    if run_param != "1":
        return "pong"

    alerts = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alerts.append(f"\ud83d\udce1 \uc870\uac74 \ucda9\uc870 \uc885\ubaa9 ({now})")

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            df.dropna(inplace=True)
            close = df['Close']
            rsi = calculate_rsi(close)
            ma20 = close.rolling(window=20).mean()

            latest_close = close.iloc[-1]
            latest_ma20 = ma20.iloc[-1]
            latest_rsi = rsi.iloc[-1]

            decisions = []
            if latest_rsi < 35:
                decisions.append("\ud83d\udd35 \uc0b4\uc544!!! (RSI<35)")
            elif latest_rsi > 65:
                decisions.append("\ud83d\udd34 \ud314\uc544!!! (RSI>65)")

            if latest_close > latest_ma20 and latest_rsi <= 65:
                decisions.append("\ud83d\udd35 \uc0b4\uc544!!! (MA20 \ub3cc\ud30c)")
            elif latest_close < latest_ma20 and latest_rsi > 35:
                decisions.append("\ud83d\udd34 \ud314\uc544!!! (MA20 \uc774\ud0c8)")

            if decisions:
                alert_text = f"\ud83d\udcc8 {ticker}\n\uc885\uac00: ${latest_close:.2f} / MA20: ${latest_ma20:.2f} / RSI: {latest_rsi:.2f}\n" + "\n".join(decisions)
                alerts.append(alert_text)
        except Exception as e:
            alerts.append(f"\u274c {ticker} \ucc98\ub9ac \uc911 \uc5d0\ub7ec: {e}")

    send_telegram_alert("\n\n".join(alerts))
    return "alert sent"
