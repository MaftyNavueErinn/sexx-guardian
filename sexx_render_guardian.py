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
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {"chat_id": TG_CHAT_ID, "text": message}
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram error: {e}")

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=window).mean()
    avg_loss = pd.Series(loss).rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return pd.Series(rsi)

@app.route("/ping")
def ping():
    run = request.args.get("run")
    if run != "1":
        return "pong"

    alert_message = f"\U0001F4E1 조건 충족 종목 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            df = df.dropna()
            close = df["Close"]
            ma20 = close.rolling(window=20).mean()
            rsi = calculate_rsi(close)

            latest_close = close.iloc[-1]
            latest_ma20 = ma20.iloc[-1]
            latest_rsi = rsi.iloc[-1]

            signals = []
            if latest_rsi > 65:
                signals.append("\U0001F534 팔아!!! (RSI>65)")
            elif latest_rsi < 35 and latest_close < latest_ma20:
                signals.append("\U0001F7E2 사!!! (RSI<35 & MA20 아래)")
            elif latest_close > latest_ma20:
                signals.append("\U0001F7E2 사!!! (MA20 돌파)")
            elif latest_close < latest_ma20:
                signals.append("\U0001F534 팔아!!! (MA20 이탈)")

            if signals:
                alert_message += f"\n\U0001F4C8 {ticker}\n종가: ${latest_close:.2f} / MA20: ${latest_ma20:.2f} / RSI: {latest_rsi:.2f}\n" + "\n".join(signals) + "\n"

        except Exception as e:
            alert_message += f"\n❌ {ticker} 처리 중 에러: {str(e)}\n"

    send_telegram_alert(alert_message)
    return "done"

if __name__ == "__main__":
    app.run(debug=True, port=10000)
