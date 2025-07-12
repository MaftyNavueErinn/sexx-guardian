import os
import time
import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from flask import Flask
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 테스트용 종목 (TSLA)
TICKER = "TSLA"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

def check_rsi_and_alert():
    df = yf.download(TICKER, period="20d", interval="1d", progress=False)

    if df.empty:
        print("데이터가 없습니다.")
        return

    close = df["Close"]
    if len(close.shape) > 1:
        close = close.squeeze()  # (20,1) 형태일 경우 1D로 변환

    ma20 = close.rolling(window=20).mean()
    try:
        rsi = RSIIndicator(close=close).rsi().iloc[-1]
    except Exception as e:
        print("RSI 계산 중 오류 발생:", e)
        return

    current_price = close.iloc[-1]
    current_ma20 = ma20.iloc[-1]

    message = f"[알림] {TICKER}\nRSI: {rsi:.2f} | 종가: {current_price:.2f} | MA20: {current_ma20:.2f}"
    print(message)

    # 타점 조건
    if rsi < 35 and current_price < current_ma20:
        send_telegram_alert(f"📉 [{TICKER}] RSI < 35 & 종가 < MA20 진입 타점!")
    elif rsi > 65 and current_price > current_ma20:
        send_telegram_alert(f"🚀 [{TICKER}] RSI > 65 & 종가 > MA20 익절 타점!")

@app.route("/ping")
def ping():
    check_rsi_and_alert()
    return "Ping received and RSI checked!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
