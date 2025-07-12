# Save the modified code as sexx_render_guardian.py
code = """
import os
import time
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

# ✅ 텔레그램 설정
TD_API = "5ccea133825e4496869229edbbfcc2a2"
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

# ✅ 감시 종목
TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

# ✅ RSI 계산 함수
def get_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ✅ 현재 실시간 가격 조회
def get_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TD_API}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200 or not res.text.strip():
            raise Exception(f"API 응답 없음 or 실패 (status={res.status_code})")
        data = res.json()
        if "price" not in data:
            raise Exception(f"price 필드 없음: {data}")
        return float(data["price"])
    except Exception as e:
        print(f"❌ {symbol} 가격 조회 실패: {e}")
        return None

# ✅ 텔레그램 메시지 전송
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print("❌ 텔레그램 전송 실패:", e)

# ✅ 핵심 분석 로직
def analyze_ticker(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        df.dropna(inplace=True)
        if df.empty or len(df) < 20:
            print(f"❌ {ticker}: 데이터 부족")
            return

        df["RSI"] = get_rsi(df)
        rsi = df["RSI"].iloc[-1]
        close = df["Close"].iloc[-1]
        ma20 = df["Close"].rolling(window=20).mean().iloc[-1]

        price = get_price(ticker)
        if price is None:
            send_telegram_message(f"⚠️ 실시간 가격 조회 실패: {ticker}")
            return

        message = None
        if rsi < 40 and close < ma20:
            message = f"🟢 [{ticker}] 매수타점 감지\\n→ RSI: {rsi:.2f} / 종가: {close:.2f} < MA20: {ma20:.2f}\\n→ 실시간가: ${price:.2f}"
        elif rsi > 65 and close > ma20:
            message = f"🔴 [{ticker}] 매도 경고\\n→ RSI: {rsi:.2f} / 종가: {close:.2f} > MA20: {ma20:.2f}\\n→ 실시간가: ${price:.2f}"

        if message:
            send_telegram_message(message)

    except Exception as e:
        print(f"❌ 분석 실패: {ticker}\\n에러: {e}")

# ✅ 전체 감시 실행
def check_alerts():
    print(f"🕒 [{datetime.now()}] 감시 시작")
    for symbol in TICKERS:
        analyze_ticker(symbol)

# ✅ Flask 서버
app = Flask(__name__)

@app.route('/')
def index():
    check_alerts()
    return "✅ 자동 감시 1회 실행 완료"

# ✅ 스케줄러 설정 (1시간마다)
scheduler = BackgroundScheduler(timezone="Asia/Seoul")
scheduler.add_job(check_alerts, "interval", hours=1)
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
"""
with open("/mnt/data/sexx_render_guardian.py", "w", encoding="utf-8") as f:
    f.write(code)

"/mnt/data/sexx_render_guardian.py"

