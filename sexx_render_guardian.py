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
        print("\ud1b5\uc2e0 \ecec\x9eec\x9e\x90\ubaa9 \uc804\uc1a1 \uc624\ub958:", e)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_rsi_ma_signals():
    signals = []
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            df.dropna(inplace=True)
            df["RSI"] = calculate_rsi(df["Close"])
            df["MA20"] = df["Close"].rolling(window=20).mean()

            latest = df.iloc[-1]
            rsi = latest["RSI"]
            close = latest["Close"]
            ma20 = latest["MA20"]

            overbought = rsi > 70
            oversold = rsi < 35
            ma20_cross_up = close > ma20 and df["Close"].iloc[-2] < df["MA20"].iloc[-2]
            ma20_cross_down = close < ma20 and df["Close"].iloc[-2] > df["MA20"].iloc[-2]

            if oversold or ma20_cross_up:
                signals.append(f"🟢 {ticker} 진입각 (RSI={rsi:.2f}, Close={close:.2f}, MA20={ma20:.2f})")
            elif overbought or ma20_cross_down:
                signals.append(f"🔴 {ticker} 과엽 경고 (RSI={rsi:.2f}, Close={close:.2f}, MA20={ma20:.2f})")
        except Exception as e:
            print(f"{ticker} 오류: {e}")
    return signals

@app.route("/ping")
def ping():
    if request.args.get("run") == "1":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        signals = get_rsi_ma_signals()
        if signals:
            msg = f"📈 감시 트리거 발생! ({now})\n\n" + "\n".join(signals)
            send_telegram_alert(msg)
        else:
            print(f"{now} - 조건 마출 종목 없음.")
        return "Ping executed"
    return "Ping OK"

if __name__ == "__main__":
    app.run(debug=True)
