# 수정된 코드 (ndarray 오류 해결)

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
    requests.post(url, data=data)

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route("/ping")
def ping():
    run_flag = request.args.get("run", "0")
    if run_flag != "1":
        return "Ping received"

    alerts = []
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 20:
                alerts.append(f"⚠ {ticker} 데이터 부족")
                continue

            close = df['Close'].astype(float)
            ma20 = close.rolling(window=20).mean()
            rsi = calculate_rsi(close)

            current_close = close.iloc[-1]
            current_ma20 = ma20.iloc[-1]
            current_rsi = rsi.iloc[-1]

            status = None
            if current_rsi < 35 and current_close < current_ma20:
                status = "📉 사!! (저점 타점)"
            elif current_rsi > 65 and current_close > current_ma20:
                status = "📈 팔아!! (고점 타점)"

            if status:
                alerts.append(f"{ticker}: {status} (RSI={current_rsi:.2f}, MA20={current_ma20:.2f}, Close={current_close:.2f})")

        except Exception as e:
            alerts.append(f"❌ {ticker} 처리 중 에러: {str(e)}")

    if alerts:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_msg = f"\n🚨 타점 알림 ({now}) 🚨\n\n" + "\n".join(alerts)
        send_telegram_alert(alert_msg)

    return "완료"

if __name__ == "__main__":
    app.run(debug=True)
