import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask
from datetime import datetime
import logging
import requests

app = Flask(__name__)

# ✅ 텔레그램 정보
_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
_CHAT_ID = "7733010521"

# ✅ 감시 종목
TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

# ✅ RSI 기준값
RSI_THRESHOLD = 40

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

# ✅ 텔레그램 메시지 전송
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{_TOKEN}/sendMessage"
    payload = {"chat_id": _CHAT_ID, "text": text}
    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            print(f"❌ 텔레그램 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 텔레그램 전송 에러: {e}")

# ✅ RSI 계산 함수
def get_rsi(close_prices, period=14):
    delta = close_prices.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ✅ 종목별 RSI 감시
def check_rsi_alerts():
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty:
                continue
            df.dropna(inplace=True)
            close = df["Close"]
            rsi = get_rsi(close).iloc[-1]
            price = close.iloc[-1]

            if rsi < RSI_THRESHOLD:
                msg = (
                    f"⚠️ [{ticker}] RSI 과매도 ({rsi:.2f}) 감지!\n"
                    f"현재가: ${price:.2f} / Max Pain: ${MAX_PAIN.get(ticker, 'N/A')}"
                )
                send_telegram_message(msg)

        except Exception as e:
            print(f"❌ {ticker} 오류: {e}")

# ✅ /ping 엔드포인트
@app.route('/ping')
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_telegram_message(f"🔔 감시 시작됨: {now}")
    check_rsi_alerts()
    return f"[{now}] Ping OK - 감시 완료"

# ✅ gunicorn 실행용 (app.run 제거)
logging.basicConfig(level=logging.INFO)
