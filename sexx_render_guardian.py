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
    payload = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("텔레그램 전송 실패:", e)

def check_rsi_ma_conditions(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        if df.empty:
            return None

        close = df["Close"]
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        ma20 = close.rolling(window=20).mean()

        last_rsi = rsi.iloc[-1]
        last_close = close.iloc[-1]
        last_ma20 = ma20.iloc[-1]

        # Debug 로그 출력
        print(f"[DEBUG] {ticker} - RSI: {last_rsi:.2f}, Close: {last_close:.2f}, MA20: {last_ma20:.2f}")

        # 값이 NaN이면 조건문 안탐
        if np.isnan(last_rsi) or np.isnan(last_close) or np.isnan(last_ma20):
            return None

        # 조건 검사
        if last_rsi < 35 and last_close < last_ma20:
            return f"✅ {ticker} - 존나 사!! (RSI={last_rsi:.1f}, 종가<{last_ma20:.2f})"
        elif last_rsi > 65 and last_close > last_ma20:
            return f"🚨 {ticker} - 씨발 팔아!! (RSI={last_rsi:.1f}, 종가>{last_ma20:.2f})"
        else:
            return None

    except Exception as e:
        return f"❌ {ticker} 처리 중 에러: {str(e)}"

@app.route("/ping")
def ping():
    run_flag = request.args.get("run")
    if run_flag != "1":
        return "Ping OK (no run)"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alerts = []

    for ticker in TICKERS:
        result = check_rsi_ma_conditions(ticker)
        if result:
            alerts.append(result)

    if alerts:
        message = f"📡 조건 충족 종목 ({now})\n" + "\n".join(alerts)
        send_telegram_alert(message)
        return message
    else:
        return f"🔍 조건 충족 종목 없음. {now}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
