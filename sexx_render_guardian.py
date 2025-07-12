# Updated version of the monitoring bot with patched get_price and alert handling
code = '''
import yfinance as yf
import requests
import pandas as pd
import time
import datetime
import pytz

# Constants
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"
TD_API = "5ccea133825e4496869229edbbfcc2a2"

# Target stocks
symbols = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO",
    "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        data = {"chat_id": TG_CHAT_ID, "text": msg}
        res = requests.post(url, data=data)
        if res.status_code != 200:
            print("텔레그램 전송 실패:", res.text)
    except Exception as e:
        print("텔레그램 전송 중 예외:", e)

def get_price(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
    try:
        res = requests.get(url)
        if res.status_code != 200:
            print(f"[{symbol}] ⚠️ 응답 실패. Status code: {res.status_code}")
            return None
        data = res.json()
        return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception as e:
        print(f"[{symbol}] ❌ 가격 가져오기 실패: {e}")
        return None

def analyze_stock(symbol):
    try:
        df = yf.download(symbol, period="20d", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            raise Exception("Not enough data")

        df["ma20"] = df["Close"].rolling(window=20).mean()
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]
        close = latest["Close"]
        ma20 = latest["ma20"]
        rsi = latest["rsi"]

        signal = ""
        if rsi < 35 and close < ma20:
            signal = f"🔻 [{symbol}] 진입각 (RSI={rsi:.2f}, 종가<{ma20:.2f})"
        elif rsi > 65 and close > ma20:
            signal = f"🔺 [{symbol}] 매도각 (RSI={rsi:.2f}, 종가>{ma20:.2f})"

        return signal
    except Exception as e:
        return f"❌ 분석 실패: {symbol}\\n에러: {e}"

def check_alerts():
    for symbol in symbols:
        print(f"분석 중: {symbol}")
        signal = analyze_stock(symbol)
        if signal:
            send_telegram(signal)
        time.sleep(1.2)  # API 과부하 방지

if __name__ == "__main__":
    print("🔥 감시 스크립트 실행됨 🔥")
    check_alerts()
'''
with open("/mnt/data/sexx_render_guardian.py", "w") as f:
    f.write(code)

"/mnt/data/sexx_render_guardian.py"
