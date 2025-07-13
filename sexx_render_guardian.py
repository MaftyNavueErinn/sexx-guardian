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
        logging.error(f"텔레그램 전송 실패: {e}")

# RSI 계산 함수
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@app.route("/ping")
def ping():
    run_flag = request.args.get("run") == "1"
    if run_flag:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"\ud83d\udcf1 \uc870\uac74 \ucda9\uc870 \uc885\ubaa9 ({now})"

        for ticker in TICKERS:
            try:
                df = yf.download(ticker, period="20d", interval="1d", progress=False)
                close = df["Close"]
                ma20 = close.rolling(window=20).mean()
                rsi = calculate_rsi(close)

                c = close.iloc[-1]
                m = ma20.iloc[-1]
                r = rsi.iloc[-1]

                action = None
                if r < 35:
                    action = "\ud83d\ude80 존나 사!!"
                elif r > 65 and c > m:
                    action = "\u274c 당장 팔아!!"

                if action:
                    message += f"\n{ticker}: {action} (종가: {c:.2f}, MA20: {m:.2f}, RSI: {r:.2f})"

            except Exception as e:
                message += f"\n\u274c {ticker} 처리 중 에러: {e}"

        send_telegram_alert(message)
    return "pong"
