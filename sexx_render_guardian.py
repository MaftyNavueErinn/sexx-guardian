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
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        logging.error(f"텔레그램 전송 에러: {e}")


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


@app.route("/ping")
def ping():
    run = request.args.get("run")
    if run != "1":
        return "pong"

    alert_message = f"\n<b>📡 조건 충초 종목 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})</b>"
    
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="2d", interval="5m", progress=False)
            df.dropna(inplace=True)

            df['RSI'] = calculate_rsi(df['Close'])
            rsi = round(df['RSI'].iloc[-1], 2)
            close_price = round(df['Close'].iloc[-1], 2)
            ma20 = round(df['Close'].rolling(window=20).mean().iloc[-1], 2)

            signal = ""
            if rsi > 65:
                signal = "🔴 <b>팔아!!!</b> (RSI>65)"
            elif close_price > ma20:
                signal = "🟢 <b>사!!!</b> (MA20 돌파)"
            elif rsi < 35:
                signal = "🟢 <b>사!!!</b> (RSI<35)"
            elif close_price < ma20:
                signal = "🔴 <b>팔아!!!</b> (MA20 이탄)"
            else:
                continue  # 조건 미충족이면 패스

            alert_message += f"\n\n📈 <b>{ticker}</b>\n종가: ${close_price} / MA20: ${ma20} / RSI: {rsi}\n{signal}"

        except Exception as e:
            alert_message += f"\n\n❌ {ticker} 처리 중 에러: {str(e)}"

    send_telegram_alert(alert_message)
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
