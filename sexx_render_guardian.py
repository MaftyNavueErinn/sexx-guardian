import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, request
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
RSI_LOW = 40
RSI_HIGH = 65

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

# ✅ 텔레그램 메시지 전송 함수
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{_TOKEN}/sendMessage"
    payload = {"chat_id": _CHAT_ID, "text": text}
    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            print(f"❌ 텔레그램 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 텔레그램 전송 오류: {e}")

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

# ✅ 알림 체크 함수
def check_alerts():
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="21d", interval="1d", progress=False, auto_adjust=True)
            if df.empty:
                continue

            df.dropna(inplace=True)
            close = df["Close"]
            volume = df["Volume"]
            rsi_series = get_rsi(close)

            if rsi_series.isna().iloc[-1]:
                continue

            price = float(close.iloc[-1])
            ma20 = float(close.rolling(20).mean().iloc[-1])
            volume_today = float(volume.iloc[-1])
            volume_ma5 = float(volume.rolling(5).mean().iloc[-1])
            rsi = float(rsi_series.iloc[-1])

            alerts = []

            if rsi < RSI_LOW:
                alerts.append(f"⚠️ RSI 과매도 ({rsi:.2f})")
            elif rsi > RSI_HIGH:
                alerts.append(f"🚨 RSI 과매수 ({rsi:.2f})")

            if price > ma20:
                alerts.append(f"📈 MA20 돌파 (${ma20:.2f})")
            elif price < ma20:
                alerts.append(f"📉 MA20 이탈 (${ma20:.2f})")

            max_pain = MAX_PAIN.get(ticker)
            if max_pain:
                gap_percent = abs(price - max_pain) / max_pain * 100
                if gap_percent >= 5:
                    alerts.append(f"💀 체산각: MaxPain ${max_pain:.2f} / 현재가 ${price:.2f}")

            if volume_today > volume_ma5 * 2:
                alerts.append(f"🔥 거래량 급등: {volume_today:,.0f} / 평균 {volume_ma5:,.0f}")

            if alerts:
                msg = f"🔍 [{ticker}] 감지됨\n" + "\n".join(alerts)
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

# ✅ 로그 설정
logging.basicConfig(level=logging.INFO)
