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

def get_rsi(data, window=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route("/ping")
def ping():
    run_check = request.args.get("run", default="0")
    if run_check != "1":
        return "Ping received, but run=1 not specified."

    alert_messages = []
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)["Close"]
            if len(df) < 20:
                alert_messages.append(f"⚠️ {ticker} 데이터 부족")
                continue

            ma20 = df.rolling(window=20).mean()
            rsi = get_rsi(df)

            close = float(df.iloc[-1])
            ma20_last = float(ma20.iloc[-1])
            rsi_last = float(rsi.iloc[-1])

            msg = f"📈 {ticker}\n종가: ${close:.2f} / MA20: ${ma20_last:.2f} / RSI: {rsi_last:.2f}\n"

            if rsi_last < 40:
                msg += "🟢 사!!! (RSI<40)\n"
            elif rsi_last > 65:
                msg += "🔴 팔아!!! (RSI>65)\n"

            if close > ma20_last:
                msg += "🟢 사!!! (MA20 돌파)\n"
            elif close < ma20_last:
                msg += "🔴 팔아!!! (MA20 이탈)\n"

            if "사!!!" in msg or "팔아!!!" in msg:
                alert_messages.append(msg)

        except Exception as e:
            alert_messages.append(f"❌ {ticker} 처리 중 에러: {e}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if alert_messages:
        final_message = f"📡 조건 충족 종목 ({timestamp})\n" + "\n".join(alert_messages)
        send_telegram_alert(final_message)

    return "Ping processed."

if __name__ == "__main__":
    app.run(debug=True, port=10000)
