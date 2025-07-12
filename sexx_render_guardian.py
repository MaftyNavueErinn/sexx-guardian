
import os
import time
import requests
import yfinance as yf
from datetime import datetime
from pytz import timezone

TD_API = "5ccea133825e4496869229edbbfcc2a2"
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

def get_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": msg}
    try:
        res = requests.post(url, data=data)
        res.raise_for_status()
    except Exception as e:
        print("❌ 텔레그램 전송 실패:", e)

def get_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TD_API}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            return float(data['price'])
        else:
            send_telegram(f"[ERROR] price API 실패 - {symbol}: HTTP {res.status_code} / {res.text}")
            return None
    except Exception as e:
        send_telegram(f"[ERROR] price API 예외 발생 - {symbol}: {e}")
        return None

def analyze_ticker(ticker):
    try:
        df = yf.download(ticker, period="90d", interval="1d", progress=False)
        df.dropna(inplace=True)
        if df.shape[0] < 60:
            raise ValueError("데이터 부족")

        rsi = get_rsi(df).iloc[-1]
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
        upper_band = df['Close'].rolling(20).mean() + 2 * df['Close'].rolling(20).std()
        lower_band = df['Close'].rolling(20).mean() - 2 * df['Close'].rolling(20).std()
        bb_lower = lower_band.iloc[-1]

        volume = df['Volume'].iloc[-1]
        volume_prev = df['Volume'].iloc[-2]
        volume_signal = volume > volume_prev * 1.5

        obv = df['Volume'].copy()
        obv[df['Close'].diff() < 0] *= -1
        obv = obv.cumsum().iloc[-1]

        signals = []

        if rsi < 40 and close < ma20:
            signals.append("📉 매수 조건(RSI<40 & 종가<MA20)")
        if rsi > 65 and close > ma20:
            signals.append("🚨 매도 조건(RSI>65 & 종가>MA20)")
        if close > ma60:
            signals.append("↗️ MA60 돌파 (추세 전환)")
        if close < bb_lower:
            signals.append("🧨 볼린저밴드 하단 이탈")
        if volume_signal:
            signals.append("🔥 거래량 급등")

        if signals:
            msg = f"[{ticker}] 시그널 발생\n"                   f"종가: {close:.2f}\nRSI: {rsi:.2f}\nMA20: {ma20:.2f}, MA60: {ma60:.2f}\n"                   + "\n".join(signals)
            send_telegram(msg)

    except Exception as e:
        print(f"❌ 분석 실패 - {ticker}: {e}")
        send_telegram(f"❌ 분석 실패: {ticker}\n에러: {e}")

def main_loop():
    while True:
        now_kst = datetime.now(timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
        send_telegram(f"⏱️ 자동감시 작동 중: {now_kst}")
        for ticker in TICKERS:
            analyze_ticker(ticker)
        time.sleep(3600)

if __name__ == "__main__":
    main_loop()
