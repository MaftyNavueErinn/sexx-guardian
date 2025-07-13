
import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask
import requests
from datetime import datetime

app = Flask(__name__)

TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

def get_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_ma(data, period=20):
    return data['Close'].rolling(window=period).mean()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": message}
    requests.post(url, json=payload)

@app.route("/ping")
def ping():
    alert_msgs = []
    for ticker in TICKERS:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        if df.empty:
            continue

        df['RSI'] = get_rsi(df)
        df['MA20'] = get_ma(df)

        rsi = df['RSI'].iloc[-1]
        close = df['Close'].iloc[-1]
        ma20 = df['MA20'].iloc[-1]

        if rsi <= 40:
            alert_msgs.append(f"{ticker} RSI 진입각: {rsi:.2f}")
        elif close > ma20 and df['Close'].iloc[-2] <= df['MA20'].iloc[-2]:
            alert_msgs.append(f"{ticker} MA20 돌파각: {close:.2f} > {ma20:.2f}")

    if alert_msgs:
        final_msg = "[🚨 진입 시그널 감지됨]
" + "
".join(alert_msgs)
        send_telegram_message(final_msg)
    return "pong", 200
