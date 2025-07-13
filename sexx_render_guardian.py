
import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask
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

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print("Failed to send message:", response.text)
    except Exception as e:
        print("Exception occurred while sending message:", str(e))

@app.route("/ping")
def ping():
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            df = df.dropna()
            if df.empty:
                print(f"{ticker} 데이터 없음")
                continue

            df["RSI"] = calculate_rsi(df)
            df["MA20"] = df["Close"].rolling(window=20).mean()

            rsi = df["RSI"].iloc[-1]
            close = df["Close"].iloc[-1]
            ma20 = df["MA20"].iloc[-1]

            if rsi <= 40:
                send_telegram_message(f"📉 {ticker} RSI 40 이하! 진입 타점 감지됨
현재 RSI: {rsi:.2f}, 종가: ${close:.2f}")
            elif close > ma20:
                send_telegram_message(f"📈 {ticker} 종가가 MA20 상향 돌파!
현재 종가: ${close:.2f}, MA20: ${ma20:.2f}")

        except Exception as e:
            send_telegram_message(f"❌ {ticker} 처리 중 에러: {str(e)}")
            print(f"Error processing {ticker}: {e}")

    return "Ping complete"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
