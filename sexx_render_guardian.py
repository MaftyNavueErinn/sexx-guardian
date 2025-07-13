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
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"텔레그램 전송 오류: {e}")


def get_rsi(close, period=14):
    delta = close.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return pd.Series(rsi, index=close.index)


@app.route("/ping")
def ping():
    run = request.args.get("run", "0") == "1"
    alert_msgs = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            df.dropna(inplace=True)

            if len(df) < 15:
                alert_msgs.append(f"⚠️ {ticker}: 데이터 부족")
                continue

            close = df['Close']
            rsi = get_rsi(close)
            ma20 = close.rolling(window=20).mean()

            latest_rsi = rsi.iloc[-1]
            latest_close = close.iloc[-1]
            latest_ma20 = ma20.iloc[-1]

            msg = f"{ticker}: RSI={latest_rsi:.2f}, 종가={latest_close:.2f}, MA20={latest_ma20:.2f}"

            if latest_rsi < 40 and latest_close < latest_ma20:
                alert_msgs.append(f"📉 [<b>사!!</b>] {ticker} 진입 타점 감지됨\n{msg}")
            elif latest_rsi > 65 and latest_close > latest_ma20:
                alert_msgs.append(f"📈 [<b>팔아!!</b>] {ticker} 청산 타점 감지됨\n{msg}")
            else:
                print(f"🔍 {ticker}: 조건 불충족")

        except Exception as e:
            alert_msgs.append(f"❌ {ticker} 처리 중 에러: {str(e)}")

    if run and alert_msgs:
        full_msg = f"🚨 <b>타점 알림 ({now})</b> 🚨\n\n" + "\n\n".join(alert_msgs)
        send_telegram_alert(full_msg)
    elif run:
        send_telegram_alert(f"🔍 조건 충족 종목 없음. {now}")

    return "pong"


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=10000)
