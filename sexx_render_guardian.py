
import os
import time
import requests
import yfinance as yf
from datetime import datetime
from pytz import timezone

TD_API = "5ccea133825e4496869229edbbfcc2a2"
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

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
        print("텔레그램 전송 실패:", e)

def analyze_ticker(ticker):
    df = yf.download(ticker, period="20d", interval="1d", progress=False)
    if df.empty or len(df) < 20:
        return

    df["RSI"] = get_rsi(df)
    close_price = df["Close"].iloc[-1]
    ma20 = df["Close"].rolling(window=20).mean().iloc[-1]
    rsi = df["RSI"].iloc[-1]

    # 진입 타점 조건
    rsi_entry = rsi < 35 and close_price < ma20
    ma_breakout = close_price > ma20

    if rsi_entry:
        msg = f"[{ticker}] 📉 RSI 진입 타점: RSI={rsi:.2f}, 종가={close_price:.2f}, MA20={ma20:.2f}"
        send_telegram_message(msg)
    elif ma_breakout:
        msg = f"[{ticker}] 🚀 MA20 돌파 진입 타점: 종가={close_price:.2f}, MA20={ma20:.2f}, RSI={rsi:.2f}"
        send_telegram_message(msg)

if __name__ == "__main__":
    now_kst = datetime.now(timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
    send_telegram_message(f"📡 감시 시작: {now_kst}")
    for ticker in TICKERS:
        try:
            analyze_ticker(ticker)
        except Exception as e:
            send_telegram_message(f"[{ticker}] 분석 실패: {e}")
