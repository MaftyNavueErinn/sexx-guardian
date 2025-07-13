from flask import Flask, request
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time
import warnings

# 경고 제거 (yfinance auto_adjust 경고 무시)
warnings.filterwarnings("ignore", category=FutureWarning)

app = Flask(__name__)

# 텔레그램 정보
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

# 감시 대상 종목
TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

# RSI 계산
def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 개별 종목 분석
def get_stock_signal(ticker):
    try:
        time.sleep(1.2)  # 서버 보호용 딜레이

        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        df.dropna(inplace=True)
        if len(df) < 20:
            return f"❌ {ticker} 데이터 부족"

        close = df['Close'].values.reshape(-1)
        ma20 = pd.Series(close).rolling(window=20).mean().values.reshape(-1)
        rsi = calculate_rsi(pd.Series(close)).values.reshape(-1)

        current_close = close[-1]
        current_ma20 = ma20[-1]
        current_rsi = rsi[-1]

        if np.isnan(current_ma20) or np.isnan(current_rsi):
            return f"❌ {ticker} 지표 계산 불가"

        message = f"\n\n📈 {ticker}\n"
        message += f"종가: ${current_close:.2f} / MA20: ${current_ma20:.2f} / RSI: {current_rsi:.2f}\n"

        if current_rsi > 65:
            message += "🔴 팔아!!! (RSI>65)"
        elif current_rsi < 40:
            message += "🟢 사!!! (RSI<40)"
        elif current_close > current_ma20:
            message += "🟢 사!!! (MA20 돌파)"
        elif current_close < current_ma20:
            message += "🔴 팔아!!! (MA20 운지)"
        else:
            message += "❓ 관망각"

        return message
    except Exception as e:
        return f"❌ {ticker} 처리 중 에러: {str(e)}"

# 텔레그램 발송 함수
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

# 핑 엔드포인트
@app.route("/ping")
def ping():
    run_alert = request.args.get("run", default="0") == "1"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"📡 조건 충족 종목 ({now})"

    for ticker in TICKERS:
        result = get_stock_signal(ticker)
        full_message += f"\n{result}"

    if run_alert:
        send_telegram_alert(full_message)

    return "pong"  # ✅ cron-job.org 실패 방지용 최소 응답

# 로컬 실행 시 포트 설정
if __name__ == "__main__":
    app.run(debug=True, port=10000)
