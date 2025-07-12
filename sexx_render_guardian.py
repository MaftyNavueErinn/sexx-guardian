import requests
import yfinance as yf
import pandas as pd
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# 니가 박으라 했던 고정값
TD_API = "5ccea133825e4496869229edbbfcc2a2"
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

SEXX_LIST = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO",
    "GOOGL", "PSTG", "SYM", "TSMC", "ASML", "AMD", "ARM"
]

def send_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=data)
    except:
        print("🚨 텔레그램 전송 실패")

def get_tech_indicators(df):
    close = df["Close"]
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    ma20 = close.rolling(window=20).mean()
    std20 = close.rolling(window=20).std()
    lower_band = ma20 - 2 * std20

    macd = close.ewm(span=12).mean() - close.ewm(span=26).mean()
    signal = macd.ewm(span=9).mean()

    volume = df["Volume"]
    vol_ma5 = volume.rolling(window=5).mean()

    return {
        "rsi": rsi.iloc[-1],
        "close": close.iloc[-1],
        "ma20": ma20.iloc[-1],
        "lower_band": lower_band.iloc[-1],
        "macd": macd.iloc[-1],
        "signal": signal.iloc[-1],
        "volume": volume.iloc[-1],
        "vol_ma5": vol_ma5.iloc[-1],
    }

def check_tickers():
    alert_msgs = []
    for ticker in SEXX_LIST:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            continue

        indi = get_tech_indicators(df)
        reasons = []

        if indi["rsi"] < 35:
            reasons.append(f"RSI {indi['rsi']:.1f}")
        if indi["close"] > indi["ma20"]:
            reasons.append(f"MA20 돌파 ({indi['close']:.2f} > {indi['ma20']:.2f})")
        if indi["close"] < indi["lower_band"]:
            reasons.append("볼밴 하단 이탈")
        if indi["macd"] > indi["signal"]:
            reasons.append("MACD 골든크로스")
        if indi["volume"] > indi["vol_ma5"] * 1.5:
            reasons.append("거래량 급등")

        if reasons:
            alert_msgs.append(f"📈 [{ticker}] 조건 감지: " + ", ".join(reasons))

    if alert_msgs:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        full_msg = f"🚨 감시 트리거 발생 ({timestamp})\n\n" + "\n".join(alert_msgs)
        send_alert(full_msg)
    else:
        print("조건 만족 없음")

@app.route("/ping", methods=["GET"])
def ping():
    check_tickers()
    return "pong", 200

if __name__ == "__main__":
    app.run()
