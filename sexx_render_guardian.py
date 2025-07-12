from datetime import datetime
import requests
import yfinance as yf
import pandas as pd
from flask import Flask, jsonify
import pytz

app = Flask(__name__)

# ====== 🔧 설정 ======
TD_API = "5ccea133825e4496869229edbbfcc2a2"
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"
WATCHLIST = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO",
    "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

# 알림 내역 캐시 (중복 방지)
notified_today = set()

# ====== 📩 텔레그램 전송 ======
def send_telegram_alert(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"⚠️ 텔레그램 전송 실패: {e}")

# ====== 📊 종목 데이터 분석 ======
def check_stock_conditions():
    now_kst = datetime.now(pytz.timezone("Asia/Seoul")).strftime('%Y-%m-%d %H:%M:%S')
    alerts = []
    
    for symbol in WATCHLIST:
        try:
            df = yf.download(symbol, period="20d", interval="1d", progress=False)
            df.dropna(inplace=True)
            if len(df) < 15:
                continue

            close = df['Close'].iloc[-1]
            volume = df['Volume'].iloc[-1]
            ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
            ma60 = df['Close'].rolling(window=60, min_periods=1).mean().iloc[-1]
            rsi = compute_rsi(df['Close'], 14).iloc[-1]
            bb_upper, bb_lower = compute_bollinger_bands(df['Close'])
            candle_today = df.iloc[-1]
            candle_prev = df.iloc[-2]
            candle_type = "🔺상승" if candle_today["Close"] > candle_today["Open"] else "🔻하락"

            cond_rsi = rsi < 35
            cond_ma20 = close > ma20
            cond_bb_break = close < bb_lower or close > bb_upper
            cond_volume_surge = volume > df['Volume'].rolling(window=10).mean().iloc[-1] * 1.8
            cond_candle_engulf = candle_today['Close'] > candle_prev['Open'] and candle_today['Open'] < candle_prev['Close']

            conditions = [
                ("📉 RSI < 35", cond_rsi),
                ("📈 종가 > MA20", cond_ma20),
                ("💥 볼린저밴드 돌파", cond_bb_break),
                ("📊 거래량 급증", cond_volume_surge),
                ("🕯️ 양봉포획", cond_candle_engulf)
            ]

            passed = [text for text, ok in conditions if ok]
            if passed and symbol not in notified_today:
                alert = f"🚨 [{now_kst}]\n{symbol} 알림 발생!\n\n" + "\n".join(passed) + f"\n📌 종가: {round(close, 2)} / MA20: {round(ma20, 2)} / RSI: {round(rsi, 1)}"
                alerts.append(alert)
                notified_today.add(symbol)
        except Exception as e:
            print(f"[{symbol}] 오류 발생: {e}")
    
    for msg in alerts:
        send_telegram_alert(msg)

# ====== 📈 RSI 계산 ======
def compute_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    avg_gain = up.rolling(window=period).mean()
    avg_loss = down.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(0)

# ====== 📉 볼린저밴드 계산 ======
def compute_bollinger_bands(series, window=20, num_std=2):
    ma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper_band = ma + num_std * std
    lower_band = ma - num_std * std
    return upper_band.iloc[-1], lower_band.iloc[-1]

# ====== 🔁 핑 URL 감시 루틴 ======
@app.route("/ping", methods=["GET", "HEAD"])
def ping():
    check_stock_conditions()
    return jsonify({"status": "ok"})

# ====== 🌐 메인 엔드포인트 ======
@app.route("/")
def root():
    return "✅ SEXX GUARDIAN ACTIVE"

# ====== 🚀 실행 ======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

