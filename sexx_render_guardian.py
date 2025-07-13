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
        logging.error(f"텔레그램 전송 실패: {e}")

def calculate_rsi(df, period: int = 14) -> pd.Series:
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route("/ping")
def ping():
    run_flag = request.args.get("run", "0") == "1"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = f"\U0001F4E1 조건 충족 종목 ({now})\n"

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)[["Close"]]
            df.columns = ["Close"]

            df["MA20"] = df["Close"].rolling(window=20).mean()
            df["RSI"] = calculate_rsi(df)

            latest = df.iloc[-1]
            close = float(latest["Close"])
            ma20 = float(latest["MA20"])
            rsi = float(latest["RSI"])

            actions = []
            if rsi < 40:
                actions.append("🟢 사!!! (RSI<40)")
            if rsi > 65:
                actions.append("🔴 팔아!!! (RSI>65)")
            if close > ma20:
                actions.append("🟢 사!!! (종가>MA20)")
            if close < ma20:
                actions.append("🔴 팔아!!! (종가<MA20)")

            if actions:
                summary += f"\n[{ticker}]\n" + "\n".join(actions) + "\n"

        except Exception as e:
            summary += f"\n❌ {ticker} 처리 중 에러: {str(e)}\n"

    if run_flag:
        send_telegram_alert(summary)
    return summary

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
