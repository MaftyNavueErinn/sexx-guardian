# 새로운 설정 적용한 전체 코드를 생성
modified_code = '''
import os
import yfinance as yf
import ta
import requests
from flask import Flask

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TELEGRAM_CHAT_ID = "7733010521"
WATCHLIST = ["TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("텔레그램 전송 오류:", e)

def check_alerts():
    for ticker in WATCHLIST:
        try:
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            if df.empty:
                print(f"{ticker} 데이터 없음.")
                continue

            df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
            df["MA20"] = df["Close"].rolling(window=20).mean()
            df["MA60"] = df["Close"].rolling(window=60).mean()
            bb = ta.volatility.BollingerBands(df["Close"])
            df["BB_H"] = bb.bollinger_hband()
            df["BB_L"] = bb.bollinger_lband()
            df["Volume_Avg"] = df["Volume"].rolling(window=10).mean()

            latest = df.iloc[-1]
            rsi = latest["RSI"]
            close = latest["Close"]
            ma20 = latest["MA20"]
            ma60 = latest["MA60"]
            bb_h = latest["BB_H"]
            bb_l = latest["BB_L"]
            volume = latest["Volume"]
            volume_avg = latest["Volume_Avg"]

            messages = []

            if rsi < 40:
                messages.append(f"#🟥 {ticker} RSI < 40 진입각: RSI={rsi:.2f}")

            if close > ma20 and df['Close'].iloc[-2] <= df['MA20'].iloc[-2]:
                messages.append(f"#🟩 {ticker} MA20 돌파: 종가={close:.2f}, MA20={ma20:.2f}")

            if close > ma60 and df['Close'].iloc[-2] <= df['MA60'].iloc[-2]:
                messages.append(f"#📈 {ticker} MA60 돌파: 종가={close:.2f}, MA60={ma60:.2f}")

            if close < bb_l:
                messages.append(f"#📉 {ticker} 볼밴 하단 이탈: 종가={close:.2f}, BB_L={bb_l:.2f}")

            if volume > volume_avg * 1.5:
                messages.append(f"#📊 {ticker} 거래량 급증: {volume/1e6:.2f}M > 평균 {volume_avg/1e6:.2f}M")

            if messages:
                combined_message = f"<b>{ticker} 경고 알림</b>\\n" + "\\n".join(messages) + f"\\n🔗 <a href='https://finance.yahoo.com/quote/{ticker}'>[차트 보기]</a> #주식 #알림"
                send_telegram_message(combined_message)

        except Exception as e:
            print(f"{ticker} 에러 발생: {e}")

@app.route('/')
def home():
    return "Hello from Guardian"

@app.route('/ping')
def ping():
    check_alerts()
    return "pong"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
'''

# 저장
file_path = "/mnt/data/sexx_render_guardian.py"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(modified_code)

file_path
