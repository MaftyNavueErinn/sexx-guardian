from pathlib import Path

# 맥스페인 제거 + RSI 과매수(>65) + MA20 이탈(<MA20) 포함해서 수정된 코드
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
    try:
        response = requests.post(url, json=payload)
        return response
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")
        return None

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

            alert_triggered = False
            message = f"📊 {ticker} 분석 결과\\n"

            if pd.notna(rsi_last) and rsi_last < 40:
                message += f"🟡 RSI 과매도: {rsi_last:.2f}\\n"
                alert_triggered = True
            elif pd.notna(rsi_last) and rsi_last > 65:
                message += f"🔴 RSI 과매수: {rsi_last:.2f}\\n"
                alert_triggered = True

            if pd.notna(close_last) and pd.notna(ma20_last):
                if close_last > ma20_last:
                    message += f"🟢 MA20 돌파: 종가 {close_last:.2f} > MA20 {ma20_last:.2f}\\n"
                    alert_triggered = True
                elif close_last < ma20_last:
                    message += f"🔻 MA20 이탈: 종가 {close_last:.2f} < MA20 {ma20_last:.2f}\\n"
                    alert_triggered = True

            if alert_triggered:
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
