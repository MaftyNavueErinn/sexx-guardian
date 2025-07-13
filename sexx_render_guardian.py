from datetime import datetime

code = '''
from flask import Flask, request
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

app = Flask(__name__)

TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

MAX_PAIN = {
    "TSLA": 305, "ORCL": 225, "MSFT": 490, "AMZN": 215,
    "NVDA": 160, "META": 700, "AAPL": 200, "AVGO": 265,
    "GOOGL": 177.5, "PSTG": 55, "SYM": 43, "TSM": 225,
    "ASML": 790, "AMD": 140, "ARM": 145
}

def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).fillna(0)
    loss = -delta.where(delta < 0, 0).fillna(0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_stock_signal(ticker):
    try:
        time.sleep(1.2)
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        df.dropna(inplace=True)
        if len(df) < 20:
            return f"❌ {ticker} 데이터 부족"

        close = df['Close']
        ma20 = close.rolling(window=20).mean()
        rsi = calculate_rsi(close)

        current_close = close.iloc[-1]
        current_ma20 = ma20.iloc[-1]
        current_rsi = rsi.iloc[-1]
        max_pain = MAX_PAIN.get(ticker, None)

        if np.isnan(current_ma20) or np.isnan(current_rsi):
            return f"❌ {ticker} 지표 계산 불가"

        message = f"\\n\\n📈 {ticker}\\n"
        message += f"종가: ${current_close:.2f} / MA20: ${current_ma20:.2f} / RSI: {current_rsi:.2f} / MaxPain: ${max_pain}\\n"

        if current_rsi > 65:
            message += "🔴 RSI>65 → 매도 경고"
        elif current_rsi < 40:
            message += "🟢 RSI<40 → 매수 진입각"
        elif current_close > current_ma20:
            message += "🟢 MA20 돌파 → 상승 추세"
        elif current_close < current_ma20:
            message += "🔴 MA20 이탈 → 하락 추세"

        if max_pain and current_close > max_pain * 1.02:
            message += f"\\n⚠️ Max Pain 상단 이탈 → 매도 압력 경계"

        return message
    except Exception as e:
        return f"❌ {ticker} 처리 중 에러: {str(e)}"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

@app.route("/ping")
def ping():
    run_alert = request.args.get("run", default="0") == "1"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"📡 조건 충족 종목 ({now})"

    for ticker in TICKERS:
        result = get_stock_signal(ticker)
        full_message += f"\\n{result}"

    if run_alert:
        send_telegram_alert(full_message)

    return "pong"

if __name__ == "__main__":
    app.run(debug=True, port=10000)
'''

with open("/mnt/data/sexx_render_guardian.py", "w") as f:
    f.write(code)

"/mnt/data/sexx_render_guardian.py"

