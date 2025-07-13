from pathlib import Path

# 수정된 감시 코드
code = """
import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, request
from datetime import datetime
import logging
import requests

app = Flask(__name__)

TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message
    }
    response = requests.post(url, json=payload)
    return response

@app.route("/ping")
def ping():
    run_check = request.args.get("run") == "1"
    if not run_check:
        return "Ping received. Append ?run=1 to execute."

    messages = []

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            df["MA20"] = df["Close"].rolling(window=20).mean()
            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df["RSI"] = 100 - (100 / (1 + rs))

            rsi_last = df["RSI"].iloc[-1]
            close_last = df["Close"].iloc[-1]
            ma20_last = df["MA20"].iloc[-1]

            if (rsi_last < 40) or (close_last > ma20_last):
                messages.append(f"📈 {ticker} ALERT\\nRSI: {rsi_last:.2f}\\nClose: {close_last:.2f}\\nMA20: {ma20_last:.2f}")

        except Exception as e:
            messages.append(f"❌ {ticker} 처리 중 에러: {str(e)}")

    if messages:
        send_telegram_alert("\\n\\n".join(messages))
        return "Alerts sent!"
    else:
        return "No alert conditions met."

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
"""

# 저장 경로
path = Path("/mnt/data/sexx_render_guardian_FIXED_FINAL_VER.py")
path.write_text(code)
path
