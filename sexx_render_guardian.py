import yfinance as yf
import requests
import time
import datetime
import pytz
import pandas as pd

# ✅ 텔레그램 알림 설정
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

# ✅ 알림 보낼 함수
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"텔레그램 전송 오류: {e}")

# ✅ RSI 계산 함수
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ✅ 감시할 종목들
TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO", "GOOGL",
    "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

# ✅ 이전 상태 저장용
previous_alerts = {}

# ✅ 분석 및 알림 함수
def analyze_and_alert():
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)
            df.dropna(inplace=True)
            df['RSI'] = calculate_rsi(df)
            ma20 = df['Close'].rolling(window=20).mean()
            close = df['Close'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            ma = ma20.iloc[-1]

            msg_prefix = f"{ticker} 종가({round(close, 2)}) / MA20({round(ma, 2)}) / RSI({round(rsi, 2)})"

            alert_triggered = False

            if rsi < 40 and close < ma:
                if previous_alerts.get(ticker) != 'BUY':
                    send_telegram_alert(f"🔴 매수 신호: {msg_prefix}\n조건: RSI<40 + 종가<MA20")
                    previous_alerts[ticker] = 'BUY'
                    alert_triggered = True

            elif rsi > 65 and close > ma:
                if previous_alerts.get(ticker) != 'SELL':
                    send_telegram_alert(f"📈 매도 신호: {msg_prefix}\n조건: RSI>65 + 종가>MA20")
                    previous_alerts[ticker] = 'SELL'
                    alert_triggered = True

            else:
                previous_alerts[ticker] = 'HOLD'

        except Exception as e:
            send_telegram_alert(f"❌ 분석 실패: {ticker}\n에러: {str(e)}")

# ✅ 기본 루프 (10분 간격)
if __name__ == "__main__":
    while True:
        try:
            now = datetime.datetime.now(pytz.timezone('US/Eastern'))
            if now.weekday() < 5 and now.hour >= 9 and now.hour <= 16:
                analyze_and_alert()
            else:
                print("비거래 시간")
        except Exception as e:
            send_telegram_alert(f"전체 루프 에러 발생: {str(e)}")
        time.sleep(600)  # 10분 간격
