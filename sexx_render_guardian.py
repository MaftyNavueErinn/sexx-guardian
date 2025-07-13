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
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"텔레그램 전송 에러: {e}")


def calculate_rsi(close, window=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def check_conditions(ticker):
    df = yf.download(ticker, period="30d", interval="1d", progress=False)
    if df.empty or len(df) < 20:
        return None

    df.dropna(inplace=True)
    close = df["Close"]
    ma20 = close.rolling(window=20).mean()
    rsi = calculate_rsi(close)

    latest_close = close.iloc[-1]
    latest_ma20 = ma20.iloc[-1]
    latest_rsi = rsi.iloc[-1]

    message_parts = []
    if latest_rsi < 35:
        message_parts.append(f"📉 {ticker}: RSI 과매도 ({latest_rsi:.2f})")
    elif latest_rsi > 65:
        message_parts.append(f"📈 {ticker}: RSI 과매수 ({latest_rsi:.2f})")

    if latest_close < latest_ma20:
        message_parts.append(f"⬇️ 종가 < MA20 ({latest_close:.2f} < {latest_ma20:.2f})")
    elif latest_close > latest_ma20:
        message_parts.append(f"⬆️ 종가 > MA20 ({latest_close:.2f} > {latest_ma20:.2f})")

    if message_parts:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[알림: {ticker}]\n" + "\n".join(message_parts) + f"\n⏰ {now}"
        return full_msg
    return None


@app.route("/ping")
def ping():
    run_flag = request.args.get("run")
    if run_flag == "1":
        alerts = []
        for ticker in TICKERS:
            try:
                alert = check_conditions(ticker)
                if alert:
                    alerts.append(alert)
                    time.sleep(1)
            except Exception as e:
                logging.error(f"{ticker} 처리 중 오류: {e}")

        if alerts:
            for msg in alerts:
                send_telegram_alert(msg)
            return "✅ 알림 전송 완료"
        else:
            return "😶 조건 만족 종목 없음"
    return "pong"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
