from datetime import datetime
from pytz import timezone

# 사용자 요청에 따라 조건을 매우 널널하게 설정한 버전의 파이썬 파일 생성
code = '''
import os
import yfinance as yf
import ta
import requests
from flask import Flask

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
WATCHLIST = ["TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("텔레그램 전송 오류:", e)

def check_alerts():
    send_telegram_message("✅ 자동 감시 시스템 정상 작동 중")

    for ticker in WATCHLIST:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            if df.empty or len(df) < 5:
                continue

            df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
            df["MA20"] = df["Close"].rolling(window=20).mean()
            df["MA60"] = df["Close"].rolling(window=60).mean()
            df["Bollinger_Lower"] = ta.volatility.BollingerBands(df["Close"]).bollinger_lband()
            df["Volume_Change"] = df["Volume"] / df["Volume"].shift(1)

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            msg = f"<b>📢 {ticker} 감시 트리거 발생</b>\\n"
            condition_met = False

            if latest["RSI"] < 60:
                msg += f"🟢 RSI 조건 통과 (RSI={latest['RSI']:.2f})\\n"
                condition_met = True

            if latest["Close"] > latest["MA20"]:
                msg += f"🟢 MA20 돌파 (Close={latest['Close']:.2f}, MA20={latest['MA20']:.2f})\\n"
                condition_met = True

            if latest["Close"] > latest["MA60"]:
                msg += f"🟢 MA60 돌파 (Close={latest['Close']:.2f}, MA60={latest['MA60']:.2f})\\n"
                condition_met = True

            if latest["Close"] < latest["Bollinger_Lower"]:
                msg += f"🟡 볼밴 하단 이탈 (Close={latest['Close']:.2f}, Lower={latest['Bollinger_Lower']:.2f})\\n"
                condition_met = True

            if latest["Volume_Change"] > 1.1:
                msg += f"🟠 거래량 급증 (Change={latest['Volume_Change']:.2f}배)\\n"
                condition_met = True

            if condition_met:
                send_telegram_message(msg)

        except Exception as e:
            print(f"{ticker} 에러 발생: {e}")

@app.route('/')
def home():
    return "Sexx Guardian Online"

@app.route('/ping')
def ping():
    check_alerts()
    return "pong"
'''

# 파일 저장
file_path = "/mnt/data/sexx_render_guardian_modified_loose.py"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)

file_path
