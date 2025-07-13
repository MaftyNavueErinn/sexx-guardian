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

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"\u274c\ufe0f 템레그램 전송 실패: {e}")

@app.route("/ping")
def ping():
    run_flag = request.args.get("run")
    if run_flag != "1":
        return "Pong"

    results = []

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            close_prices = df["Close"]
            ma20 = close_prices.rolling(window=20).mean()
            rsi = calculate_rsi(close_prices)

            latest_close = close_prices.iloc[-1]
            latest_ma20 = ma20.iloc[-1]
            latest_rsi = rsi.iloc[-1]

            action = []

            if latest_rsi > 65:
                action.append("\ud83d\udd34 팔아!!! (RSI>65)")
            elif latest_rsi < 35:
                action.append("\ud83d\udfe2 사!!! (RSI<35)")

            if latest_close > latest_ma20:
                action.append("\ud83d\udfe2 사!!! (MA20 돌파)")
            elif latest_close < latest_ma20:
                action.append("\ud83d\udd34 팔아!!! (MA20 이탁)")

            results.append(f"\n\ud83d\udcc8 <b>{ticker}</b>\n종가: ${latest_close:.2f} / MA20: ${latest_ma20:.2f} / RSI: {latest_rsi:.2f}\n" + "\n".join(action))

        except Exception as e:
            results.append(f"\n\u274c {ticker} 처리 중 에러: {e}")

    if results:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_message = f"\ud83d\udce1 <b>\uc870건 충출 종목</b> ({now})\n" + "".join(results)
        send_telegram_alert(final_message)

    return "Done"
