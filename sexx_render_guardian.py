import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, request
from datetime import datetime
import logging
import requests

app = Flask(__name__)

# Telegram 설정
TOKEN = "<YOUR_TELEGRAM_BOT_TOKEN>"
CHAT_ID = "<YOUR_CHAT_ID>"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"텔레그램 전송 오류: {e}")

# 감시 종목
TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

# Max Pain 예시 (수동 입력)
MAX_PAIN = {
    "TSLA": 315, "ORCL": 125, "MSFT": 450, "AMZN": 190, "NVDA": 130,
    "META": 530, "AAPL": 220, "AVGO": 270, "GOOGL": 180, "PSTG": 65,
    "SYM": 52, "TSM": 185, "ASML": 1200, "AMD": 155, "ARM": 160
}

def calculate_rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_conditions(ticker, df):
    try:
        rsi = calculate_rsi(df).iloc[-1]
        close = df["Close"].iloc[-1]
        ma20 = df["Close"].rolling(window=20).mean().iloc[-1]
        max_pain = MAX_PAIN.get(ticker, None)

        alert_triggered = False
        reasons = []

        if rsi > 65:
            reasons.append("📈 RSI 과매수")
            alert_triggered = True
        elif rsi < 40:
            reasons.append("📉 RSI 과매도")
            alert_triggered = True

        if close > ma20:
            reasons.append("🔼 MA20 돌파")
            alert_triggered = True
        elif close < ma20:
            reasons.append("🔽 MA20 이탈")
            alert_triggered = True

        if max_pain:
            gap = abs(close - max_pain) / max_pain * 100
            if gap >= 5:
                reasons.append(f"🎯 MaxPain 괴리 {gap:.1f}%")
                alert_triggered = True

        return alert_triggered, reasons, rsi, close, ma20
    except Exception as e:
        print(f"❌ {ticker} 조건 체크 오류: {e}")
        return False, [], None, None, None

@app.route("/ping")
def ping():
    run_flag = request.args.get("run")
    if run_flag == "1":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        send_telegram_message(f"🔔 감시 시작됨: {now}")
        for ticker in TICKERS:
            try:
                df = yf.download(ticker, period="20d", interval="1d", progress=False)
                if df.empty:
                    continue
                alert, reasons, rsi, close, ma20 = check_conditions(ticker, df)
                if alert:
                    msg = f"🚨 {ticker} 조건 충족\n"
                    msg += f"종가: {close:.2f} / MA20: {ma20:.2f} / RSI: {rsi:.2f}\n"
                    msg += "\n".join(reasons)
                    send_telegram_message(msg)
            except Exception as e:
                print(f"❌ {ticker} 오류: {e}")
        return "OK"
    return "Ping only"

if __name__ == "__main__":
    app.run(debug=True, port=10000)
