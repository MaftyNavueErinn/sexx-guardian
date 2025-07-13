from pathlib import Path

# 잘못된 open 경로 문제 수정: /mnt/data 경로 사용하지 않고, 배포 시 필요 없는 라인 제거
# 그리고 Max Pain 출력 포함된 알림 템플릿을 포함시킨 코드로 다시 생성

code = """
from flask import Flask, request
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime

app = Flask(__name__)

TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

# ✅ 수동 Max Pain
MAX_PAIN = {
    "TSLA": 310,
    "ORCL": 225,
    "MSFT": 490,
    "AMZN": 215,
    "NVDA": 160,
    "META": 700,
    "AAPL": 200,
    "AVGO": 265,
    "GOOGL": 177.5,
    "PSTG": 55,
    "SYM": 43,
    "TSM": 225,
    "ASML": 790,
    "AMD": 140,
    "ARM": 145
}

def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_signals():
    messages = []
    for ticker in TICKERS:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        if df.empty or len(df) < 15:
            continue

        close = df["Close"]
        rsi = calculate_rsi(close).iloc[-1]
        ma20 = close.rolling(window=20).mean().iloc[-1]
        current_price = close.iloc[-1]
        max_pain = MAX_PAIN.get(ticker, "N/A")

        signal = f"📈 {ticker}\\n종가: ${current_price:.2f} / MA20: ${ma20:.2f} / RSI: {rsi:.2f} / MaxPain: ${max_pain}\\n"

        if rsi > 65:
            signal += "🔴 팔아!!! (RSI>65)"
        elif rsi < 35:
            signal += "🟢 사!!! (RSI<35)"
        elif current_price > ma20:
            signal += "🟢 사!!! (MA20 돌파)"
        elif current_price < ma20:
            signal += "🔴 팔아!!! (MA20 운지)"

        if max_pain != "N/A" and isinstance(max_pain, (int, float)):
            if current_price > max_pain * 1.03:
                signal += "\\n⚠️ Max Pain 상단 이탈 → 매도 압력 경계"

        messages.append(signal)
    return messages

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

@app.route("/ping")
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"📡 조건 충족 종목 ({now})\\n\\n"
    signals = get_signals()
    if signals:
        full_message = header + "\\n\\n".join(signals)
        send_to_telegram(full_message)
        return full_message
    else:
        return "조건 충족 종목 없음."

app.run()
"""

path = Path("/mnt/data/sexx_render_guardian.py")
path.write_text(code)
path
