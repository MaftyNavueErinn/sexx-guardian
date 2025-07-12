import os
import time
import requests
import yfinance as yf
from datetime import datetime
from pytz import timezone

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

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        res = requests.post(url, data=data)
        res.raise_for_status()
    except Exception as e:
        print("❌ 텔레그램 전송 실패:", e)

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
            signals.append("📉 [매수] RSI<40 & 종가<MA20")
        if rsi > 65 and close > ma20:
            signals.append("🚨 [매도] RSI>65 & 종가>MA20")
        if close > ma60:
            signals.append("↗️ 추세 전환: MA60 돌파")
        if close < bb_lower:
            signals.append("🧨 볼밴 하단 이탈 (과매도 경고)")
        if volume_signal:
            signals.append(f"🔥 거래량 급등: 전일대비 {volume / volume_prev:.1f}배")

        if signals:
            msg = f"📡 [{ticker}] 트레이딩 시그널 감지\n" \
                  f"📍종가: ${close:.2f}\n📈 RSI: {rsi:.2f}\n" \
                  f"MA20: {ma20:.2f}, MA60: {ma60:.2f}\n\n" + "\n".join(signals)
            send_telegram_message(msg)
            print(f"✅ {ticker} 시그널 전송 완료")

    except Exception as e:
        err_msg = f"❌ 분석 실패: {ticker}\n에러: {str(e)}"
        print(err_msg)
        send_telegram_message(err_msg)

def main_loop():
    while True:
        now_kst = datetime.now(timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
        send_telegram_message(f"🕐 [감시 시작] {now_kst} 기준 자동 트레이딩 감시 시작")
        print(f"📌 {now_kst} 기준 감시 시작")
        for ticker in TICKERS:
            analyze_ticker(ticker)
        time.sleep(3600)

if __name__ == "__main__":
    main_loop()
