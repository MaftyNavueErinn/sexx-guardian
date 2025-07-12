import yfinance as yf
import pandas as pd
from flask import Flask
import requests
from ta.momentum import RSIIndicator

app = Flask(__name__)

# 💥 텔레그램 정보
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

# 💥 감시할 종목 목록 (쎆쓰 풀버전)
TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO",
    "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

# ✅ RSI 계산 함수
def calculate_rsi(series, period=14):
    rsi = RSIIndicator(close=series, window=period)
    return rsi.rsi().iloc[-1]

# ✅ 텔레그램 전송 함수
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": message}
    requests.post(url, data=payload)

# ✅ 알림 감시 루틴
def check_alerts():
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            close = df['Close']
            rsi = calculate_rsi(close)

            # 💥 테스트 조건: RSI > 10이면 무조건 알림
            if rsi > 10:
                send_telegram(f"🔥 [TEST 알림] {ticker} RSI: {rsi:.2f} 조건 만족!")

        except Exception as e:
            print(f"{ticker} 처리 실패: {e}")

# ✅ /ping 엔드포인트 → UptimeRobot 주기 호출
@app.route("/ping")
def ping():
    check_alerts()
    return "pong"

# ✅ 루트 경로 접근 시도
@app.route("/")
def index():
    return "SEXX GUARDIAN ONLINE"

# ✅ 앱 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
