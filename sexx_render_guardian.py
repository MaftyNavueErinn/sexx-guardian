import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, request
from datetime import datetime
import logging
import requests
from pathlib import Path

app = Flask(__name__)

TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

RSI_PERIOD = 14
MA_PERIOD = 20
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 40


def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        logging.error(f"Telegram send error: {e}")


def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))


def analyze_stock(ticker):
    df = yf.download(ticker, period="20d", interval="1d", progress=False)
    if df.empty or len(df) < RSI_PERIOD:
        return None

    df['RSI'] = calculate_rsi(df['Close'], RSI_PERIOD)
    df['MA20'] = df['Close'].rolling(window=MA_PERIOD).mean()
    rsi = df['RSI'].iloc[-1]
    close = df['Close'].iloc[-1]
    ma20 = df['MA20'].iloc[-1]

    ma_slope = df['MA20'].iloc[-1] - df['MA20'].iloc[-2]

    conditions = []
    if rsi < RSI_OVERSOLD:
        conditions.append("📉 RSI 과매도")
    if rsi > RSI_OVERBOUGHT:
        conditions.append("📈 RSI 과매수")
    if close < ma20:
        conditions.append("📉 종가 < MA20")
    if close > ma20:
        conditions.append("📈 종가 > MA20")
    if ma_slope < 0:
        conditions.append("🔻 MA20 하락 중")

    if conditions:
        msg = f"[{ticker}] 조건 감지됨!\nRSI: {rsi:.2f}, 종가: {close:.2f}, MA20: {ma20:.2f}\n" + ", ".join(conditions)
        return msg
    return None


@app.route("/ping")
def ping():
    run_param = request.args.get("run", default="0")
    triggered = False

    if run_param == "1":
        triggered = True

    if triggered:
        alerts = []
        for ticker in TICKERS:
            try:
                result = analyze_stock(ticker)
                if result:
                    alerts.append(result)
            except Exception as e:
                logging.error(f"Error analyzing {ticker}: {e}")

        if alerts:
            final_msg = "\n\n".join(alerts)
            send_telegram_alert(f"🚨 자동 감시 알림 🚨\n{final_msg}")
            return {"status": "alert_sent", "alerts": alerts}

    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)

# 파일 존재 여부 확인용 코드 추가 (에러 방지용)
code = "# Dummy code to satisfy file write logic"
path = Path("/mnt/data/sexx_render_guardian.py")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(code)
