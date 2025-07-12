from flask import Flask, jsonify, request
import yfinance as yf
import pandas as pd
import requests

# === Telegram 설정 ===
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"
TG_API = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"

# === 감시 대상 종목 ===
TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO",
    "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

app = Flask(__name__)

def fetch_data(ticker):
    df = yf.download(ticker, period="20d", interval="1d", progress=False)
    df["MA20"] = df["Close"].rolling(window=20).mean()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def check_condition(ticker, df):
    latest = df.iloc[-1]
    close = latest["Close"]
    ma20 = latest["MA20"]
    rsi = latest["RSI"]

    alerts = []

    # 조건 예시
    if rsi < 35 and close < ma20:
        alerts.append(f"📉 {ticker}: RSI {rsi:.1f}, 종가 {close:.2f} < MA20 {ma20:.2f} → 매수 타점 가능성")
    elif rsi > 65 and close > ma20:
        alerts.append(f"📈 {ticker}: RSI {rsi:.1f}, 종가 {close:.2f} > MA20 {ma20:.2f} → 매도 타점 가능성")

    return alerts

def send_telegram(msg):
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": msg
    }
    requests.post(TG_API, data=payload)

@app.route("/ping", methods=["GET"])
def ping():
    all_alerts = []
    for ticker in TICKERS:
        try:
            df = fetch_data(ticker)
            alerts = check_condition(ticker, df)
            all_alerts.extend(alerts)
        except Exception as e:
            print(f"{ticker} 에러 발생: {e}")

    if all_alerts:
        message = "\n".join(all_alerts)
        send_telegram(f"📡 감시 결과:\n{message}")
    return jsonify({"status": "checked", "alerts_sent": len(all_alerts)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
