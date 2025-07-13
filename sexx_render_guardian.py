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
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return pd.Series(rsi, index=close.index)

def check_conditions(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            raise ValueError("데이터 부족")

        df['RSI'] = calculate_rsi(df['Close'])
        ma20 = df['Close'].rolling(window=20).mean()

        latest_rsi = df['RSI'].iloc[-1]
        latest_close = df['Close'].iloc[-1]
        latest_ma20 = ma20.iloc[-1]

        alert_messages = []

        if latest_rsi < 40:
            alert_messages.append(f"📉 {ticker}: RSI 진입 타점 감지됨 (RSI={latest_rsi:.2f})")
        if latest_close > latest_ma20:
            alert_messages.append(f"📈 {ticker}: MA20 돌파 감지됨 (Close={latest_close:.2f} > MA20={latest_ma20:.2f})")

        if alert_messages:
            send_telegram_alert("\n".join(alert_messages))

    except Exception as e:
        send_telegram_alert(f"❌ {ticker} 처리 중 에러: {e}")

@app.route("/ping")
def ping():
    run_param = request.args.get("run")
    if run_param == "1":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        send_telegram_alert(f"🔔 감시 시작됨: {now}")
        for ticker in TICKERS:
            check_conditions(ticker)
        return "Ping executed"
    return "Ping OK"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=10000)
