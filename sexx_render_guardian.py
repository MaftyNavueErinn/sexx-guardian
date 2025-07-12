# 수정된 버전을 생성하여 저장
corrected_code = """
import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask
from datetime import datetime
import logging
import requests

app = Flask(__name__)

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

RSI_THRESHOLD = 40

# Max Pain 수동 등록
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

# 텔레그램 알림 설정
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            print(f"❌ 텔레그램 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 텔레그램 전송 에러: {e}")

def get_rsi(close_prices, period=14):
    delta = close_prices.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(window=period, min_periods=1).mean()
    ma_down = down.rolling(window=period, min_periods=1).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_tickers():
    messages = []
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 20:
                raise ValueError("Not enough data")

            close = df['Close']
            rsi_series = get_rsi(close)
            rsi = rsi_series.iloc[-1]
            close_price = close.iloc[-1]
            ma20_series = close.rolling(window=20).mean()
            ma20 = ma20_series.iloc[-1]

            if np.isnan(rsi) or np.isnan(ma20):
                raise ValueError("RSI or MA20 is NaN")

            mp = MAX_PAIN.get(ticker, None)
            mp_str = f" | MaxPain: {mp}" if mp else ""

            if rsi < RSI_THRESHOLD or close_price > ma20:
                msg = (
                    f"📡 [실전 감시] {ticker}\\n"
                    f"RSI: {rsi:.2f} | 종가: {close_price:.2f} | MA20: {ma20:.2f}{mp_str}"
                )
                messages.append(msg)

        except Exception as e:
            messages.append(f"⚠️ {ticker} 에러: {str(e)}")
    return messages

@app.route('/ping')
def ping():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"⏰ Ping 수신됨: {now}")
    send_telegram_message(f"🚀 Ping 수신됨: {now}")

    results = check_tickers()
    if results:
        for msg in results:
            print(msg)
            send_telegram_message(msg)
    else:
        send_telegram_message("😶 감지된 종목 없음 (RSI < 40 or MA20 돌파 없음)")

    return "Ping OK\\n"

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=10000)
"""

file_path = "/mnt/data/sexx_render_guardian.py"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(corrected_code)

file_path
