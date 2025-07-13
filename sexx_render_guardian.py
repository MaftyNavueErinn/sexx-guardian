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
        "text": message.encode('utf-8', 'ignore').decode('utf-8')
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route("/ping")
def ping():
    run = request.args.get("run", default="0")
    if run == "1":
        messages = [f"[조건 충족 종목] ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"]
        for ticker in TICKERS:
            try:
                df = yf.download(ticker, period="20d", interval="1d", progress=False)
                if df.empty or len(df) < 15:
                    continue

                close = df['Close']
                ma20 = close.rolling(window=20).mean()
                rsi = get_rsi(close)

                latest_close = close.iloc[-1]
                latest_ma20 = ma20.iloc[-1]
                latest_rsi = rsi.iloc[-1]

                signals = []
                if latest_rsi > 65:
                    signals.append("[🔴 팔아] (RSI > 65)")
                elif latest_rsi < 35:
                    signals.append("[🟢 사] (RSI < 35)")
                elif latest_close > latest_ma20:
                    signals.append("[🟢 사] (MA20 돌파)")
                elif latest_close < latest_ma20:
                    signals.append("[🔴 팔아] (MA20 이탈)")

                msg = f"{ticker}: 종가={latest_close:.2f}, MA20={latest_ma20:.2f}, RSI={latest_rsi:.2f} \n" + " ".join(signals)
                messages.append(msg)

            except Exception as e:
                messages.append(f"{ticker}: 오류 발생 - {e}")

        alert_message = "\n\n".join(messages)
        send_telegram_alert(alert_message)
        return "알림 전송 완료"
    else:
        return "pong"
