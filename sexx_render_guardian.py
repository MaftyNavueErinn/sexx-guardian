import os
import time
import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from flask import Flask
import requests

app = Flask(__name__)

# 테스트용 토큰 & 채팅 ID (하드코딩)
TELEGRAM_BOT_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TELEGRAM_CHAT_ID = "7733010521"

# 테스트용 종목 (TSLA)
TICKER = "TSLA"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, data=data)
    print("텔레그램 응답:", response.status_code, response.text)

def check_rsi_and_alert():
    print("✅ check_rsi_and_alert() 실행됨")
    df = yf.download(TICKER, period="20d", interval="1d", progress=False)

    if df.empty:
        print("❌ 데이터가 없습니다.")
        return

    close = df["Close"]
    if len(close.shape) > 1:
        close = close.squeeze()

    ma20 = close.rolling(window=20).mean()
    try:
        rsi = RSIIndicator(close=close).rsi().iloc[-1]
    except Exception as e:
        print("RSI 계산 중 오류 발생:", e)
        return

    current_price = close.iloc[-1]
    current_ma20 = ma20.iloc[-1]

    print(f"[{TICKER}] RSI: {rsi:.2f}, 종가: {current_price:.2f}, MA20: {current_ma20:.2f}")

    # 💥 테스트용: 조건 무시하고 무조건 알람
    send_telegram_alert(f"[TEST] RSI 강제 트리거\n{TICKER} - RSI: {rsi:.2f} | 종가: {current_price:.2f} | MA20: {current_ma20:.2f}")

@app.route("/ping")
def ping():
    print("🚨 /ping 호출됨")
    check_rsi_and_alert()
    return "Ping received and RSI checked!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
