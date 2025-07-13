import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, request
from datetime import datetime
import logging
import requests
from bs4 import BeautifulSoup

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
        print(f"텔레그램 전송 실패: {e}")

def get_max_pain(ticker):
    try:
        url = f"https://www.marketchameleon.com/Overview/{ticker}/OptionChain/"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.find("td", string="Max Pain")
        if text and text.find_next_sibling("td"):
            return text.find_next_sibling("td").text.strip()
    except Exception as e:
        print(f"[MaxPain] {ticker} 긁기 실패: {e}")
    return "N/A"

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route("/ping")
def ping():
    triggered = []

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 20:
                continue

            df["RSI"] = calculate_rsi(df["Close"])
            df["MA20"] = df["Close"].rolling(window=20).mean()

            rsi = df["RSI"].iloc[-1]
            close = df["Close"].iloc[-1]
            ma20 = df["MA20"].iloc[-1]
            ma_drop = df["MA20"].iloc[-1] < df["MA20"].iloc[-2]

            signal = []

            if rsi < 35 and close < ma20:
                signal.append("📉 과매도 + MA20 아래 (진입각)")
            elif rsi > 65 and close > ma20:
                signal.append("🚨 과매수 + MA20 위 (청산 신호)")
            elif rsi < 35:
                signal.append("🔻 RSI 과매도")
            elif rsi > 65:
                signal.append("🔺 RSI 과매수")

            if close > ma20:
                signal.append("📈 MA20 상단")
            elif close < ma20:
                signal.append("📉 MA20 하단")

            if ma_drop:
                signal.append("🔻 MA20 하락세")

            if signal:
                max_pain = get_max_pain(ticker)
                message = f"[{ticker}]\n가격: ${close:.2f}\nRSI: {rsi:.2f} / MA20: {ma20:.2f}\n맥스페인: {max_pain}\n신호: {' | '.join(signal)}"
                send_telegram_alert(message)
                triggered.append(ticker)

        except Exception as e:
            send_telegram_alert(f"❌ {ticker} 처리 중 에러: {e}")

    return f"✅ 감시 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 트리거: {', '.join(triggered)}"

if __name__ == "__main__":
    app.run(debug=True, port=10000)
