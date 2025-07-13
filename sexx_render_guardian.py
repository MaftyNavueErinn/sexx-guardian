import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, request
from datetime import datetime
import logging
import requests

app = Flask(__name__)

# ✅ 테러그램 정보
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

# ✅ 테램 메시지 전송
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{_TOKEN}/sendMessage"
    payload = {"chat_id": _CHAT_ID, "text": text}
    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            print(f"❌ 테램 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 테램 전송 오류: {e}")

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

# ✅ 종목별 감시 로직

def check_alerts():
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty:
                continue
            df.dropna(inplace=True)

            close = df["Close"]
            volume = df["Volume"]

            rsi = get_rsi(close).iloc[-1]
            price = close.iloc[-1]
            volume_today = volume.iloc[-1]
            volume_yesterday = volume.iloc[-2]
            volume_ma5 = volume.rolling(5).mean().iloc[-1]

            # RSI 거리
            if rsi < RSI_THRESHOLD:
                msg = (
                    f"⚠️ [{ticker}] RSI 과매도 ({rsi:.2f}) 감지!\n"
                    f"현재가: ${price:.2f} / Max Pain: ${MAX_PAIN.get(ticker, 'N/A')}"
                )
                send_telegram_message(msg)

            # 거래량 까다지
            if volume_today > volume_yesterday * 2 and volume_today > volume_ma5 * 2:
                msg = (
                    f"🔥 [{ticker}] 거래\uub7c9 까다지!\n"
                    f"오른가: ${price:.2f} / 거래\uub7c9: {volume_today:,}"
                )
                send_telegram_message(msg)

        except Exception as e:
            print(f"❌ {ticker} 오류: {e}")

# ✅ /ping 엔드포인트
@app.route('/ping')
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if request.args.get("run") == "1":
        send_telegram_message(f"🔔 감시 시작됨: {now}")
        check_alerts()
        return f"[{now}] Ping OK - 감시 완료"
    else:
        return f"[{now}] Ping OK - 자동 전송 X"

# ✅ gunicorn 실행용
logging.basicConfig(level=logging.INFO)
