# Save the final version of the script as 'sexx_render_guardian.py' in the accessible directory

code = '''
import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, request
import requests

app = Flask(__name__)

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

MAX_PAIN = {
    "TSLA": 305, "ORCL": 135, "MSFT": 455, "AMZN": 200,
    "NVDA": 125, "META": 495, "AAPL": 210, "AVGO": 265,
    "GOOGL": 175, "PSTG": 65, "SYM": 120, "TSM": 165,
    "ASML": 1170, "AMD": 155, "ARM": 145
}

TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

def get_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("텔레그램 에러:", e)

@app.route("/ping")
def ping():
    run_check = request.args.get("run") == "1"
    if run_check:
        send_telegram_alert("🔔 감시 시작됨: " + time.strftime("%Y-%m-%d %H:%M:%S"))
        for ticker in TICKERS:
            try:
                df = yf.download(ticker, period="20d", interval="1d", progress=False)
                if df.empty or len(df) < 15:
                    continue

                close = df["Close"]
                ma20 = close.rolling(window=20).mean()
                rsi = get_rsi(close)

                rsi_last = rsi.iloc[-1]
                ma20_last = ma20.iloc[-1]
                close_last = close.iloc[-1]
                max_pain = MAX_PAIN.get(ticker)

                messages = []

                if rsi_last < 40:
                    messages.append(f"📉 <b>{ticker}</b> RSI <b>{rsi_last:.2f}</b> (과매도)")
                elif rsi_last > 65:
                    messages.append(f"📈 <b>{ticker}</b> RSI <b>{rsi_last:.2f}</b> (과매수)")

                if close_last < ma20_last:
                    messages.append(f"❗️ <b>{ticker}</b> MA20 이탈 ({close_last:.2f} < {ma20_last:.2f})")
                elif close_last > ma20_last:
                    messages.append(f"✅ <b>{ticker}</b> MA20 돌파 ({close_last:.2f} > {ma20_last:.2f})")

                if max_pain and abs(close_last - max_pain) / max_pain > 0.05:
                    messages.append(f"⚠️ <b>{ticker}</b> Max Pain 괴리율 5% 초과 ({close_last:.2f} vs {max_pain})")

                if messages:
                    send_telegram_alert("\\n".join(messages))

            except Exception as e:
                send_telegram_alert(f"❌ <b>{ticker} 오류:</b> {e}")
    return "pong"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
'''

file_path = "/mnt/data/sexx_render_guardian.py"
with open(file_path, "w") as f:
    f.write(code)

file_path
