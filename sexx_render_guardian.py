
from flask import Flask, request
import threading
import time
import requests

app = Flask(__name__)

TD_API = "5ccea133825e4496869229edbbfcc2a2"
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

TICKERS = ["TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO",
           "GOOGL", "TSM", "ASML", "AMD"]
RSI_THRESHOLD = 40
INTERVAL = "1day"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except:
        pass

def get_rsi(symbol):
    url = f"https://api.twelvedata.com/rsi?symbol={symbol}&interval={INTERVAL}&apikey={TD_API}"
    try:
        res = requests.get(url).json()
        return float(res['values'][0]['rsi'])
    except:
        return None

def get_ema(symbol):
    url = f"https://api.twelvedata.com/ema?symbol={symbol}&interval={INTERVAL}&time_period=20&apikey={TD_API}"
    try:
        res = requests.get(url).json()
        return float(res['values'][0]['ema'])
    except:
        return None

def get_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TD_API}"
    try:
        res = requests.get(url).json()
        return float(res['price'])
    except:
        return None

def guardian_loop():
    while True:
        for symbol in TICKERS:
            try:
                rsi = get_rsi(symbol)
                ma20 = get_ema(symbol)
                close = get_price(symbol)
                if None in (rsi, ma20, close):
                    continue
                if rsi < RSI_THRESHOLD:
                    send_telegram(f"⚠️ {symbol} RSI={rsi:.2f} < {RSI_THRESHOLD} 진입각 감지!")
                if close > ma20:
                    send_telegram(f"📈 {symbol} 종가({close:.2f}) > MA20({ma20:.2f}) 돌파! 상승 신호!")
            except:
                continue
        time.sleep(300)  # 5분 주기

@app.route("/", methods=["GET"])
def ping():
    return "OK", 200

if __name__ == "__main__":
    threading.Thread(target=guardian_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
