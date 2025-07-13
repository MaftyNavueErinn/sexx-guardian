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
        print(f"텔레그램 전송 오류: {e}")

def calculate_rsi(close_prices, period=14):
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_conditions():
    messages = [f"\ud83d\udce1 \uc870\uac74 \ucda9\ucd09 \uc885\ubaa9 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"]
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)[["Close"]]
            df = df.dropna()
            df["RSI"] = calculate_rsi(df["Close"])
            df["MA20"] = df["Close"].rolling(window=20).mean()
            latest = df.iloc[-1]
            close = latest["Close"]
            ma20 = latest["MA20"]
            rsi = latest["RSI"]

            status = []
            # 우선순위 분기: RSI > 65이면 무조건 "팔아!!!"
            if rsi > 65:
                status.append("\ud83d\udd34 \ud314\uc544!!! (RSI>65)")
            elif rsi < 40:
                status.append("\ud83d\udfe2 \uc0ac!!! (RSI<40)")
            elif close > ma20:
                status.append("\ud83d\udfe2 \uc0ac!!! (MA20 \ub3cc\ud30c)")
            elif close < ma20:
                status.append("\ud83d\udd34 \ud314\uc544!!! (MA20 \uc774\ud0c8)")

            if status:
                msg = f"\n\ud83d\udcc8 {ticker}\n\uc885\uac00: ${close:.2f} / MA20: ${ma20:.2f} / RSI: {rsi:.2f}\n" + "\n".join(status)
                messages.append(msg)
        except Exception as e:
            messages.append(f"\u274c {ticker} \ucc98\ub9ac \uc911 \uc5d0\ub7ec: {str(e)}")

    final_message = "\n".join(messages)
    send_telegram_alert(final_message)

@app.route("/ping")
def ping():
    if request.args.get("run") == "1":
        check_conditions()
        return "\uc870\uac74 \ud310\ubc95 \uc644\ub8cc"
    return "pong"

if __name__ == "__main__":
    app.run(debug=True, port=10000)
