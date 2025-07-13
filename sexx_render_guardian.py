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
    requests.post(url, data=payload)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze_ticker(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)["Close"]
        df = df.dropna()
        if len(df) < 20:
            return f"⚠️ {ticker}: 데이터 부족"

        close_price = df.iloc[-1]
        ma20 = df.rolling(window=20).mean().iloc[-1]
        rsi = calculate_rsi(df).iloc[-1]

        signal = f"\n<b>\U0001F4C8 {ticker}</b>"
        signal += f"\n종가: ${close_price:.2f} / MA20: ${ma20:.2f} / RSI: {rsi:.2f}"

        # RSI 조건 우선 적용
        if rsi > 65:
            signal += f"\n🔴 <b>팔아!!!</b> (RSI>65)"
        elif rsi < 35:
            signal += f"\n🟢 <b>사!!!</b> (RSI<35)"
        elif close_price > ma20:
            signal += f"\n🟢 <b>사!!!</b> (MA20 돌파)"
        elif close_price < ma20:
            signal += f"\n🔴 <b>팔아!!!</b> (MA20 이탈)"

        return signal

    except Exception as e:
        return f"❌ {ticker} 처리 중 에러: {str(e)}"

@app.route("/ping")
def ping():
    run = request.args.get("run")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    messages = [f"\U0001F4E1 조건 충족 종목 ({now})"]

    for ticker in TICKERS:
        result = analyze_ticker(ticker)
        messages.append(result)

    # 한 덩어리로 묶어서 전송
    full_message = "\n".join(messages)

    if run == "1":
        send_telegram_alert(full_message)

    return "Ping Success!"
