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
        requests.post(url, json=payload)
    except Exception as e:
        logging.error(f"텔레그램 전송 실패: {e}")


@app.route("/ping")
def ping():
    run_flag = request.args.get("run")
    if run_flag != "1":
        return "pong"

    results = []

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 20:
                raise ValueError("데이터 부족")

            close = df["Close"]
            delta = close.diff()
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)

            avg_gain = pd.Series(gain).rolling(window=14).mean()
            avg_loss = pd.Series(loss).rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            ma20 = close.rolling(window=20).mean()

            last_close = close.iloc[-1]
            last_ma20 = ma20.iloc[-1]
            last_rsi = rsi.iloc[-1]

            signals = []

            if last_rsi > 65:
                signals.append("\U0001F534 팔아!!! (RSI>65)")
            elif last_rsi < 35:
                signals.append("\U0001F7E2 사!!! (RSI<35)")
            else:
                signals.append("- RSI 평범")

            if last_close > last_ma20:
                signals.append("\U0001F7E2 사!!! (MA20 돌파)")
            elif last_close < last_ma20:
                signals.append("\U0001F534 팔아!!! (MA20 이탈)")
            else:
                signals.append("- MA20 근처")

            result = f"\n\U0001F4C8 {ticker}\n종가: ${last_close:.2f} / MA20: ${last_ma20:.2f} / RSI: {last_rsi:.2f}\n" + "\n".join(signals)
            results.append(result)

        except Exception as e:
            results.append(f"\n❌ {ticker} 처리 중 에러: {e}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"\U0001F4E1 조건 충족 종목 ({now})" + "".join(results)
    send_telegram_alert(full_message)

    return "pong"
