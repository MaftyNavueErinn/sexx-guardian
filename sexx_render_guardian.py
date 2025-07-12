
import os
import time
import requests
import yfinance as yf
from datetime import datetime
from pytz import timezone
from flask import Flask

TO_API = "SAMPLE_TELEGRAM_API"
TG_TOKEN = "SAMPLE_BOT_TOKEN"
TG_CHAT_ID = "SAMPLE_CHAT_ID"

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

def get_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print("❌텔레그램 전송 실패:", e)

def analyze_ticker(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        df.dropna(inplace=True)
        rsi = get_rsi(df).iloc[-1]
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]

        message = None
        if rsi < 35 and close < ma20:
            message = f"🟢 {ticker} 매수 타점: RSI {rsi:.2f}, 종가 {close:.2f} < MA20 {ma20:.2f}"
        elif rsi > 65 and close > ma20:
            message = f"🔴 {ticker} 매도 타점: RSI {rsi:.2f}, 종가 {close:.2f} > MA20 {ma20:.2f}"

        if message:
            send_telegram_message(message)

    except Exception as e:
        print(f"❌ 분석 실패 - {ticker}: {e}")

app = Flask(__name__)

@app.route('/')
def index():
    for ticker in TICKERS:
        analyze_ticker(ticker)
    return "🔥쎆쓰 감시 완료"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
