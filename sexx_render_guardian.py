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
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": message.encode('utf-8').decode('utf-8'),
            "parse_mode": "HTML"
        }
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram error:", e)

@app.route("/ping")
def ping():
    run = request.args.get("run")
    if run:
        check_conditions()
    return "pong"

def check_conditions():
    messages = [f"📡 조건 충조 종목 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"]
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty:
                continue

            close = df['Close']
            delta = close.diff()
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            avg_gain = pd.Series(gain).rolling(window=14).mean()
            avg_loss = pd.Series(loss).rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            rsi_latest = round(rsi.iloc[-1], 2)
            ma20 = round(df['Close'].rolling(window=20).mean().iloc[-1], 2)
            close_price = round(close.iloc[-1], 2)

            flags = []
            if rsi_latest > 65:
                flags.append("\ud83d\udd34 \ud314\uc544!!! (RSI>=65)")
            elif rsi_latest < 35:
                flags.append("\ud83d\udfe2 \uc0ac!!! (RSI<35)")

            if close_price > ma20:
                flags.append("\ud83d\udfe2 \uc0ac!!! (MA20 \ub3cc파)")
            elif close_price < ma20:
                flags.append("\ud83d\udd34 \ud314\uc544!!! (MA20 \uc774탁)")

            if flags:
                msg = f"\n\ud83d\udcc8 <b>{ticker}</b>\n\uc885가: ${close_price} / MA20: ${ma20} / RSI: {rsi_latest}\n" + "\n".join(flags)
                messages.append(msg)

        except Exception as e:
            messages.append(f"\n❌ {ticker} 처리 중 에러: {str(e)}")

    final_message = "\n".join(messages)
    send_telegram_alert(final_message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
