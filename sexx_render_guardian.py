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
    payload = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("텔레그램 전송 에러:", e)


def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


@app.route("/ping")
def ping():
    run_param = request.args.get("run")
    if run_param != "1":
        return "pong"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_message = f"\n\ud83d\udce1 \uc870\uac74 \ucda9\ucd08 \uc885\ubaa9 ({now})\n"

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="5d", interval="5m", progress=False)
            if df.empty:
                alert_message += f"\u274c {ticker} \ub370\uc774\ud130 \uc5c6\uc74c\n"
                continue

            close = df["Close"]
            ma20 = close.rolling(window=20).mean()
            rsi = calculate_rsi(close)

            last_close = close.iloc[-1]
            last_ma20 = ma20.iloc[-1]
            last_rsi = rsi.iloc[-1]

            status = ""
            if last_rsi > 65:
                status = "\ud83d\udd34 \ud314\uc544!!! (RSI>65)"
            elif last_close > last_ma20:
                status = "\ud83d\udfe2 \uc0ac!!! (MA20 \ub3cc\ud30c)"
            elif last_rsi < 35:
                status = "\ud83d\udfe2 \uc0ac!!! (RSI<35)"
            elif last_close < last_ma20:
                status = "\ud83d\udd34 \ud314\uc544!!! (MA20 \uc774\ud0c4)"

            alert_message += f"\n\ud83d\udcc8 {ticker}\n\uc885\uac00: ${last_close:.2f} / MA20: ${last_ma20:.2f} / RSI: {last_rsi:.2f}\n{status}\n"

        except Exception as e:
            alert_message += f"\u274c {ticker} \ucc98\ub9ac \uc911 \uc5d0\ub7ec: {str(e)}\n"

    send_telegram_alert(alert_message)
    return "done"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
