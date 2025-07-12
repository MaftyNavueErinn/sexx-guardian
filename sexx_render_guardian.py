# 먼저 고급 감시 시스템의 핵심 구조를 설계하기 위한 코드 템플릿을 생성
# RSI, MA20, MA60, Bollinger Bands, MACD, OBV 등 포함
# 외부 API 호출 없이 구조만 설계

core_script = '''
import requests
import time
import numpy as np

TD_API = "YOUR_TWELVE_DATA_API_KEY"
TG_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TG_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

TICKERS = ["TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO",
           "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"]

INTERVAL = "1h"
RSI_THRESHOLD = 40

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

        # RSI 계산
        delta = np.diff(closes)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = np.mean(gain[-14:])
        avg_loss = np.mean(loss[-14:])
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))

        # 이동평균
        ma20 = np.mean(closes[-20:])
        ma60 = np.mean(closes[-60:]) if len(closes) >= 60 else ma20

        # 볼린저밴드
        std = np.std(closes[-20:])
        upper_band = ma20 + (2 * std)
        lower_band = ma20 - (2 * std)

        # MACD
        ema12 = np.mean(closes[-12:])
        ema26 = np.mean(closes[-26:])
        macd = ema12 - ema26
        signal = np.mean([ema12 - ema26 for _ in range(9)])

        # OBV (단순 계산)
        obv = 0
        for i in range(1, len(values)):
            close_now = float(values[i-1]['close'])
            close_prev = float(values[i]['close'])
            volume = float(values[i-1]['volume'])
            if close_now > close_prev:
                obv += volume
            elif close_now < close_prev:
                obv -= volume

        return rsi, ma20, ma60, closes[-1], upper_band, lower_band, macd, signal, obv
    except Exception as e:
        print(f"[{symbol}] Error: {e}")
        return None

def check_conditions(symbol):
    data = get_ta_data(symbol)
    if data is None:
        return
    rsi, ma20, ma60, close, upper, lower, macd, signal, obv = data
    msg = f"📊 [{symbol}] Close: {close:.2f}, RSI: {rsi:.1f}, MA20: {ma20:.2f}, MA60: {ma60:.2f}, MACD: {macd:.2f}, Signal: {signal:.2f}, OBV: {obv:.0f}"
    print(msg)

    alerts = []
    if rsi < RSI_THRESHOLD:
        alerts.append(f"⚠️ RSI 과매도 구간 진입: {rsi:.1f}")
    if close > ma20 and close > ma60:
        alerts.append("📈 MA20 & MA60 동시 돌파")
    if close < lower:
        alerts.append("🔻 볼린저밴드 하단 이탈")
    if close > upper:
        alerts.append("🔺 볼린저밴드 상단 돌파")
    if macd > signal:
        alerts.append("🟢 MACD 골든크로스 발생")

    if alerts:
        alert_msg = f"[{symbol}] 진입각 감지!\n" + "\n".join(alerts)
        send_telegram(alert_msg)

if __name__ == "__main__":
    while True:
        for symbol in TICKERS:
            check_conditions(symbol)
        time.sleep(3600)  # 1시간마다 감시
'''

file_path = "/mnt/data/sexx_trader_guardian_pro.py"
with open(file_path, "w") as f:
    f.write(core_script)

file_path
d
