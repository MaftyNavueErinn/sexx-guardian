from pathlib import Path

# sexx_render_guardian.py의 완전한 실전 풀옵션 버전
code = """
import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, request
from datetime import datetime
import logging
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        return response
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")
        return None

def get_max_pain(ticker):
    try:
        url = f"https://www.marketchameleon.com/Overview/{ticker}/OptionChain/"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.find("td", string="Max Pain")
        if text and text.find_next_sibling("td"):
            return text.find_next_sibling("td").text.strip()
    except:
        pass
    return "N/A"

@app.route("/ping")
def ping():
    run_check = request.args.get("run") == "1"
    if not run_check:
        return "Ping received. Append ?run=1 to execute."

    messages = []

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False, auto_adjust=False)

            if df.empty or len(df) < 20:
                messages.append(f"⚠️ {ticker} 데이터 부족")
                continue

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

            max_pain = get_max_pain(ticker)

            alert_triggered = False
            message = f"📊 {ticker} 분석 결과\\n"

            if pd.notna(rsi_last) and rsi_last < 40:
                message += f"🟡 RSI 과매도: {rsi_last:.2f}\\n"
                alert_triggered = True
            if pd.notna(close_last) and pd.notna(ma20_last) and close_last > ma20_last:
                message += f"🟢 종가 > MA20 돌파: {close_last:.2f} > {ma20_last:.2f}\\n"
                alert_triggered = True

            if alert_triggered:
                message += f"📍 Max Pain: {max_pain}"
                messages.append(message)

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

path = Path("/mnt/data/sexx_render_guardian.py")
path.write_text(code)
path
