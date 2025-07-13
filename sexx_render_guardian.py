# sexx_render_guardian.py 수정

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
        requests.post(url, json=payload)
    except Exception as e:
        print("텔레그램 전송 오류:", e)


def compute_rsi(data, period=14):
    delta = np.diff(data)
    up = delta.clip(min=0)
    down = -1 * delta.clip(max=0)
    ma_up = pd.Series(up).rolling(window=period).mean()
    ma_down = pd.Series(down).rolling(window=period).mean()
    rsi = 100 - (100 / (1 + ma_up / ma_down))
    return rsi.iloc[-1]


@app.route("/ping")
def ping():
    run = request.args.get("run", "0") == "1"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    messages = [f"\ud83d\udce1 \uc870\uac74 \ucda9\ucd08 \uc885\ubaa9 ({now})"]
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 20:
                messages.append(f"\u274c {ticker} \uac00\uae30 \ubaa8\ub450\uae4c\uae30\uae4c\uc9c0 \ubcf4\ub294\ub370 \uc774\uc0c1\ud558\ub2e4")
                continue

            close_prices = df["Close"].values.ravel()
            ma20 = df["Close"].rolling(window=20).mean().values.ravel()
            rsi = compute_rsi(close_prices)
            close = close_prices[-1]
            ma20_val = ma20[-1]

            signal = []
            if rsi > 65:
                signal.append("\ud83d\udd34 <b>\ud314\uc544!!!</b> (RSI>65)")
            elif rsi < 35:
                signal.append("\ud83d\udfe2 <b>\uc0ac!!!</b> (RSI<35)")
            elif close > ma20_val:
                signal.append("\ud83d\udfe2 <b>\uc0ac!!!</b> (MA20 \ub3cc\ud30c)")
            elif close < ma20_val:
                signal.append("\ud83d\udd34 <b>\ud314\uc544!!!</b> (MA20 \uc774\ud0c4)")

            msg = f"\n\ud83d\udcc8 <b>{ticker}</b>\n\uc885\uac00: ${close:.2f} / MA20: ${ma20_val:.2f} / RSI: {rsi:.2f}"
            for s in signal:
                msg += f"\n{s}"

            messages.append(msg)
        except Exception as e:
            messages.append(f"\u274c {ticker} \ucc98\ub9ac \uc911 \uc5d0\ub7ec: {str(e)}")

    full_message = "\n".join(messages)
    if run:
        send_telegram_alert(full_message)
    return "pong"


if __name__ == "__main__":
    app.run(debug=True, port=10000)
