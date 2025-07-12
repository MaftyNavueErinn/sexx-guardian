import yfinance as yf
from ta.momentum import RSIIndicator
from flask import Flask
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TELEGRAM_CHAT_ID = "7733010521"

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

TEST_FORCE_ALERT = True  # ✅ 테스트 강제 발사 모드 ON

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, data=data)
        print("📨 텔레그램 응답:", response.status_code, response.text)
    except Exception as e:
        print("❌ 텔레그램 전송 실패:", e)

def check_all_rsi():
    print("🚨 [RSI 감시 시작]")

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="20d", interval="1d", progress=False)

            if df.empty:
                msg = f"⚠️ [TEST] {ticker} 데이터 없음 → 강제 테스트 알람"
                send_telegram_alert(msg)
                print(msg)
                continue

            close = df["Close"]
            rsi = RSIIndicator(close=close).rsi().iloc[-1]
            ma20 = close.rolling(window=20).mean().iloc[-1]
            price = close.iloc[-1]

            print(f"[{ticker}] RSI: {rsi:.2f} | 종가: {price:.2f} | MA20: {ma20:.2f}")

            if TEST_FORCE_ALERT:
                msg = (
                    f"📣 [TEST] RSI 강제 트리거\n"
                    f"{ticker} - RSI: {rsi:.2f} | 종가: {price:.2f} | MA20: {ma20:.2f}"
                )
                send_telegram_alert(msg)

        except Exception as e:
            msg = f"❌ [TEST] {ticker} 처리 실패 → 예외 발생: {e}"
            print(msg)
            send_telegram_alert(msg)

@app.route("/ping")
def ping():
    print("📡 /ping 수신됨 → 테스트 알람 + 감시 시작")
    send_telegram_alert("💣 [TEST] /ping 감지됨 → 감시 루틴 작동 시작")
    check_all_rsi()
    return "Ping OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
