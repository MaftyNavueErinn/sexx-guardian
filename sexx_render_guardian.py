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
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram error:", e)


@app.route("/ping")
def ping():
    run = request.args.get("run")
    if run == "1":
        alerts = ["\ud83d\udcc1 \uc870\uac74 \ucda9\ucd09 \uc885\ubaa9 ({} UTC)".format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))]
        for ticker in TICKERS:
            try:
                df = yf.download(ticker, period="20d", interval="1d", progress=False)
                close = df["Close"]
                ma20 = close.rolling(window=20).mean()
                delta = close.diff()
                gain = delta.where(delta > 0, 0.0)
                loss = -delta.where(delta < 0, 0.0)
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

                last_close = close.iloc[-1]
                last_ma20 = ma20.iloc[-1]
                last_rsi = rsi.iloc[-1]

                action = ""
                if last_rsi > 65:
                    action = "\ud83d\udd34 \ud314\uc544!!! (RSI>65)"
                elif last_rsi < 35:
                    action = "\ud83d\udfe2 \uc0ac!!! (RSI<35)"
                elif last_close > last_ma20:
                    action = "\ud83d\udfe2 \uc0ac!!! (MA20 \ub3cc\ud30c)"
                elif last_close < last_ma20:
                    action = "\ud83d\udd34 \ud314\uc544!!! (MA20 \uc774\ud0c8)"

                alerts.append(
                    f"\n\ud83d\udcc8 {ticker}\n\uc885\uac00: ${last_close:.2f} / MA20: ${last_ma20:.2f} / RSI: {last_rsi:.2f}\n{action}"
                )
            except Exception as e:
                alerts.append(f"\n\u274c {ticker} \ucc98\ub9ac \uc911 \uc5d0\ub7ec: {str(e)}")

        send_telegram_alert("\n".join(alerts))
        return "Alert sent"
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
