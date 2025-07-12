from pathlib import Path

# 수정된 코드 내용
code = '''
import time
import requests
import yfinance as yf
from datetime import datetime

# ✅ 아래 두 줄만 너의 정보로 수정하면 된다
TD_API = "5ccea133825e4496869229edbbfcc2a2"
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("텔레그램 전송 에러:", e)

def get_rsi(data, window=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_ma(data, window):
    return data.rolling(window=window).mean()

def check_signal(ticker):
    df = yf.download(ticker, period="20d", interval="1d", progress=False)
    if df.empty:
        return

    close = df["Close"]
    rsi = get_rsi(close).iloc[-1]
    ma20 = get_ma(close, 20).iloc[-1]
    current_price = close.iloc[-1]

    msg = f"{ticker} 현재가: ${current_price:.2f} | RSI: {rsi:.2f} | MA20: ${ma20:.2f}\\n"

    signal_triggered = False
    if rsi < 35 and current_price < ma20:
        msg += "[매수 타점 포착 - RSI < 35 & 종가 < MA20]\\n"
        signal_triggered = True
    elif rsi > 65 and current_price > ma20:
        msg += "[매도 타점 포착 - RSI > 65 & 종가 > MA20]\\n"
        signal_triggered = True

    if signal_triggered:
        full_msg = msg + "[🚨 진입 신호 감지!]"
        send_telegram_message(full_msg)

if __name__ == "__main__":
    TICKERS = ["TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "ORCL", "AVGO"]
    for ticker in TICKERS:
        check_signal(ticker)
'''

# 파일로 저장
file_path = Path("/mnt/data/sexx_render_guardian_fixed.py")
file_path.write_text(code)

file_path.name
