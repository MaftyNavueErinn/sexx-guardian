
import requests
import time
import numpy as np

TD_API = "5ccea133825e4496869229edbbfcc2a2"
TG_TOKEN = "Y7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

TICKERS = ["TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO",
           "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"]

INTERVAL = "1h"
RSI_THRESHOLD = 35

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_ta_data(symbol):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={INTERVAL}&outputsize=100&apikey={TD_API}"
        res = requests.get(url).json()
        values = res['values']
        closes = np.array([float(item['close']) for item in values])[::-1]
        volumes = np.array([float(item['volume']) for item in values])[::-1]

        # RSI
        delta = np.diff(closes)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = np.mean(gain[-14:])
        avg_loss = np.mean(loss[-14:])
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))

        # MA
        ma20 = np.mean(closes[-20:])
        ma60 = np.mean(closes[-60:]) if len(closes) >= 60 else ma20

        # Bollinger Bands
        std = np.std(closes[-20:])
        upper_band = ma20 + (2 * std)
        lower_band = ma20 - (2 * std)

        # MACD
        ema12 = np.mean(closes[-12:])
        ema26 = np.mean(closes[-26:])
        macd = ema12 - ema26
        signal = np.mean([ema12 - ema26 for _ in range(9)])

        # OBV
        obv = 0
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv += volumes[i]
            elif closes[i] < closes[i-1]:
                obv -= volumes[i]

        return {
            "rsi": rsi,
            "ma20": ma20,
            "ma60": ma60,
            "close": closes[-1],
            "upper": upper_band,
            "lower": lower_band,
            "macd": macd,
            "signal": signal,
            "obv": obv
        }
    except Exception as e:
        print(f"[{symbol}] Error: {e}")
        return None

def check_conditions(symbol):
    data = get_ta_data(symbol)
    if data is None:
        return

    msg = f"""
📊 [{symbol}] 감시 보고서
🔹 종가: {data['close']:.2f}
🔹 RSI: {data['rsi']:.1f}
🔹 MA20: {data['ma20']:.2f}
🔹 MA60: {data['ma60']:.2f}
🔹 MACD: {data['macd']:.2f} / Signal: {data['signal']:.2f}
🔹 OBV: {data['obv']:.0f}
"""

    alerts = []
    if data['rsi'] < RSI_THRESHOLD:
        alerts.append(f"⚠️ RSI 과매도 ({data['rsi']:.1f})")
    if data['close'] > data['ma20'] and data['close'] > data['ma60']:
        alerts.append("🚀 MA20/MA60 돌파")
    if data['close'] < data['lower']:
        alerts.append("📉 볼밴 하단 이탈")
    if data['close'] > data['upper']:
        alerts.append("📈 볼밴 상단 돌파")
    if data['macd'] > data['signal']:
        alerts.append("🟢 MACD 골든크로스")

    if alerts:
full_msg = msg + "\n✅ 감시 완료: 주가 조건 충족됨!"
🚨 진입 신호 감지:
" + "
".join(alerts)
        send_telegram(full_msg)

if __name__ == "__main__":
    while True:
        for symbol in TICKERS:
            check_conditions(symbol)
        time.sleep(3600)
