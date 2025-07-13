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
        logging.error(f"Telegram error: {e}")

def get_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route("/ping")
def ping():
    run = request.args.get("run")
    alert_message = f"\U0001F4E1 조건 충족 종목 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
    triggered = False

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 15:
                raise ValueError("Not enough data")

            close = df['Close']
            ma20 = close.rolling(window=20).mean()
            rsi = get_rsi(close)

            last_rsi = rsi.iloc[-1]
            last_close = close.iloc[-1]
            last_ma20 = ma20.iloc[-1]

            if last_rsi < 35 and last_close < last_ma20:
                alert_message += f"✅ {ticker}: 사!! (RSI={last_rsi:.2f}, 종가={last_close:.2f} < MA20={last_ma20:.2f})\n"
                triggered = True
            elif last_rsi > 65 and last_close > last_ma20:
                alert_message += f"❌ {ticker}: 팔아!! (RSI={last_rsi:.2f}, 종가={last_close:.2f} > MA20={last_ma20:.2f})\n"
                triggered = True

        except Exception as e:
            alert_message += f"❌ {ticker} 처리 중 에러: {e}\n"

    if triggered:
        send_telegram_alert(alert_message)

    return "pong"

if __name__ == "__main__":
    app.run(debug=True)
