from pathlib import Path

# 수정된 sexx_render_guardian.py 생성
modified_code = '''
import os
import pandas as pd
import yfinance as yf
import requests
from flask import Flask
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from ta.trend import SMAIndicator

app = Flask(__name__)

TICKERS = ["TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"]
RSI_THRESHOLD = 40
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def fetch_data(ticker):
    df = yf.download(ticker, period="20d", interval="1d", progress=False)
    if len(df) < 20:
        return None
    df["RSI"] = RSIIndicator(df["Close"]).rsi()
    df["MA20"] = SMAIndicator(df["Close"], window=20).sma_indicator()
    df["MA60"] = SMAIndicator(df["Close"], window=60).sma_indicator()
    bb = BollingerBands(df["Close"], window=20)
    df["BB_Lower"] = bb.bollinger_lband()
    df["VolumeAvg"] = df["Volume"].rolling(window=5).mean()
    return df

def check_conditions(ticker, df):
    latest = df.iloc[-1]
    conditions = {
        "RSI<40": latest["RSI"] < RSI_THRESHOLD,
        "Close<MA20": latest["Close"] < latest["MA20"],
        "Close>MA20": latest["Close"] > latest["MA20"],
        "Close>MA60": latest["Close"] > latest["MA60"],
        "Close<BB_Lower": latest["Close"] < latest["BB_Lower"],
        "Volume>Avg": latest["Volume"] > latest["VolumeAvg"]
    }
    triggered = [k for k, v in conditions.items() if v]
    return triggered

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

@app.route("/ping")
def ping():
    messages = []
    for ticker in TICKERS:
        try:
            df = fetch_data(ticker)
            if df is None:
                continue
            triggered = check_conditions(ticker, df)
            if triggered:
                last_close = df.iloc[-1]["Close"]
                message = f"🚨 *{ticker} 알림 트리거!* 🚨\\n조건: {', '.join(triggered)}\\n📉 종가: ${last_close:.2f}\\n[🔗 트레이딩뷰](https://www.tradingview.com/symbols/{ticker})"
                send_telegram_message(message)
                messages.append(f"{ticker}: {', '.join(triggered)}")
        except Exception as e:
            print(f"Error for {ticker}: {e}")
    return "\\n".join(messages) if messages else "✅ 모든 종목 이상 없음."

if __name__ == "__main__":
    os.makedirs("/mnt/data", exist_ok=True)
    file_path = "/mnt/data/sexx_render_guardian.py"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("This is a test file created at runtime.\\n")
    app.run(host="0.0.0.0", port=10000)
'''

output_path = "/mnt/data/sexx_render_guardian.py"
Path(output_path).write_text(modified_code, encoding="utf-8")

output_path
