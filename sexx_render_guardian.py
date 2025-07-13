import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, request
from datetime import datetime
import logging
import requests

app = Flask(__name__)

TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdgDqXi3yGQ"
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
        logging.error(f"❌ 텔레그램 전송 실패: {e}")

def get_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route("/ping")
def ping():
    run_flag = request.args.get("run")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_telegram_alert(f"🔔 감시 시작됨: {now}")

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 15:
                raise ValueError("데이터 부족")

            df["RSI"] = get_rsi(df["Close"])
            df["MA20"] = df["Close"].rolling(window=20).mean()

            rsi = df["RSI"].iloc[-1].item()
            close = df["Close"].iloc[-1].item()
            ma20 = df["MA20"].iloc[-1].item()

            signal = []

            if rsi <= 40:
                signal.append("🟢 RSI 낮음 - 사!!")
            if rsi >= 65:
                signal.append("🔴 RSI 높음 - 팔아!!")
            if close > ma20:
                signal.append("🟢 MA20 돌파 - 사!!")
            if close < ma20:
                signal.append("🔴 MA20 이탈 - 팔아!!")

            if signal:
                msg = f"[{ticker}]\n종가: {close:.2f}\nRSI: {rsi:.2f} / MA20: {ma20:.2f}\n\n" + "\n".join(signal)
                send_telegram_alert(msg)

        except Exception as e:
            send_telegram_alert(f"❌ {ticker} 처리 중 에러: {str(e)}")

    return "pong"

if __name__ == "__main__":
    app.run(debug=True, port=10000)
