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
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"텔레그램 전송 오류: {e}")

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route("/ping")
def ping():
    run_param = request.args.get("run")
    if run_param != "1":
        return "pong"

    message_lines = [f"\U0001F4E1 조건 충족 종목 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"]

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            df = df.dropna()
            close = df['Close'].astype(float)
            ma20 = close.rolling(window=20).mean()
            rsi = calculate_rsi(close)

            rsi_value = float(rsi.iloc[-1])
            ma20_value = float(ma20.iloc[-1])
            close_value = float(close.iloc[-1])

            line = f"[{ticker}] RSI: {rsi_value:.2f} / 종가: {close_value:.2f} / MA20: {ma20_value:.2f}"

            if rsi_value < 40:
                line += " → 📉 사!!"
            elif rsi_value > 65 and close_value > ma20_value:
                line += " → 📈 팔아!!"
            elif close_value > ma20_value:
                line += " → ☝️ MA20 돌파"
            elif close_value < ma20_value:
                line += " → 👇 MA20 이탈"
            else:
                continue

            message_lines.append(line)

        except Exception as e:
            message_lines.append(f"❌ {ticker} 처리 중 에러: {str(e)}")

    send_telegram_alert("\n".join(message_lines))
    return "알림 전송됨"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
