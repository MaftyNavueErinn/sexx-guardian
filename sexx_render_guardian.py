from pathlib import Path

code = '''
import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask
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

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period, min_periods=1).mean()
    avg_loss = pd.Series(loss).rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_technical_indicators(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            return None, None, None

        close = df["Close"]
        rsi = calculate_rsi(close).iloc[-1]
        ma20 = close.rolling(window=20).mean().iloc[-1]
        latest_close = close.iloc[-1]

        return rsi, ma20, latest_close
    except Exception as e:
        logging.error(f"Error getting indicators for {ticker}: {e}")
        return None, None, None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

@app.route('/ping', methods=['GET'])
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_telegram_message(f"🔔 감시 시작됨: {now}")

    for ticker in TICKERS:
        try:
            rsi, ma20, close = get_technical_indicators(ticker)
            if rsi is None or ma20 is None or close is None:
                continue

            if rsi <= 40:
                send_telegram_message(f"⚠️ *{ticker} RSI 진입각!* RSI: {rsi:.2f} / 종가: {close:.2f}")
            elif close > ma20:
                send_telegram_message(f"📈 *{ticker} MA20 돌파!* 종가: {close:.2f} > MA20: {ma20:.2f}")
        except Exception as e:
            send_telegram_message(f"❌ {ticker} 처리 중 에러: {str(e)}")

    return "pong", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
'''

path = Path("/mnt/data/sexx_render_guardian.py")
path.write_text(code)
path.name
