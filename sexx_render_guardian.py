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

logging.basicConfig(level=logging.INFO)

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        logging.error(f"텔레그램 전송 실패: {e}")

def get_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_signals():
    alert_list = []

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 15:
                continue

            df['RSI'] = get_rsi(df)
            ma20 = df['Close'].rolling(window=20).mean()
            rsi = df['RSI'].iloc[-1]
            close = df['Close'].iloc[-1]
            ma20_last = ma20.iloc[-1]

            # 사!! 조건
            if rsi < 40 and close < ma20_last:
                alert_list.append(f"[사!!] {ticker} - RSI: {rsi:.2f}, 종가: {close:.2f}, MA20: {ma20_last:.2f}")
            # 팔아!! 조건
            elif rsi > 65 and close > ma20_last:
                alert_list.append(f"[팔아!!] {ticker} - RSI: {rsi:.2f}, 종가: {close:.2f}, MA20: {ma20_last:.2f}")

        except Exception as e:
            logging.error(f"{ticker} 처리 중 에러: {e}")

    return alert_list

@app.route("/ping")
def ping():
    if request.args.get("run") == "1":
        logging.info("/ping 호출됨 - 감시 루틴 시작")
        alerts = check_signals()
        if alerts:
            message = "\n".join(alerts)
            send_telegram_alert("🚨 알림 요약 🚨\n" + message)
        else:
            send_telegram_alert("✅ 감시 완료 - 조건 해당 없음")
        return "Ping complete"
    return "OK"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
