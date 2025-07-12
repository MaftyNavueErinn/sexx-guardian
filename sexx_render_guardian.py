import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import time
import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler

# ✅ 텔레그램 봇 설정 (직접 박아넣음)
TOKEN = '6202697932:AAGFi2qgQlMlq_zc4ShWMoVRAJHZHRSUpco'
CHAT_ID = '-1002182411738'

# ✅ 감시할 종목 목록 (쎆쓰)
TICKERS = [
    'TSLA', 'ORCL', 'MSFT', 'AMZN', 'NVDA', 'META', 'AAPL', 'AVGO',
    'GOOGL', 'PSTG', 'SYM', 'TSM', 'ASML', 'AMD', 'ARM'
]

# ✅ RSI 계산 함수
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = -delta.clip(upper=0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ✅ 종목 조건 체크
def check_conditions(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        df.dropna(inplace=True)

        if len(df) < 20:
            return f"⛔ 데이터 부족: {ticker}"

        df['ma20'] = df['Close'].rolling(window=20).mean()
        df['rsi'] = calculate_rsi(df)

        close = df['Close'].iloc[-1]
        ma20 = df['ma20'].iloc[-1]
        rsi = df['rsi'].iloc[-1]

        alert_msg = f"📈 <b>{ticker}</b> 조건 도달\n"
        triggered = False

        if pd.notna(rsi) and rsi < 40:
            alert_msg += f"- RSI < 40 (현재: {rsi:.2f})\n"
            triggered = True
        if pd.notna(ma20) and close > ma20:
            alert_msg += f"- 종가 > MA20 (Close: {close:.2f} > MA20: {ma20:.2f})\n"
            triggered = True

        return alert_msg if triggered else None

    except Exception as e:
        return f"❌ 분석 실패: {ticker}\n에러: {str(e)}"

# ✅ 텔레그램 전송
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

# ✅ 감시 루프
def monitor_stocks():
    now = datetime.datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"⏰ [{now}] 감시 실행")
    for ticker in TICKERS:
        result = check_conditions(ticker)
        if result:
            send_telegram_message(result)

# ✅ 스케줄러
scheduler = BackgroundScheduler(timezone='Asia/Seoul')
scheduler.add_job(monitor_stocks, 'interval', hours=1)
scheduler.start()

# ✅ 실행
print("🔥 주식 감시 시스템 작동 시작 (쎆쓰 전 종목 모니터링 중)...")
try:
    while True:
        time.sleep(3600)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
