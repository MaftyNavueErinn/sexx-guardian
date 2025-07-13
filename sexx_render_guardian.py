from flask import Flask, request
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time
import warnings

# 경고 제거
warnings.filterwarnings("ignore", category=FutureWarning)

app = Flask(__name__)

# 텔레그램 설정
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"

# 감시 대상 종목
TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

# 수동 Max Pain
MAX_PAIN = {
    "TSLA": 310, "ORCL": 225, "MSFT": 490, "AMZN": 215, "NVDA": 160,
    "META": 700, "AAPL": 200, "AVGO": 265, "GOOGL": 177.5, "PSTG": 55,
    "SYM": 43, "TSM": 225, "ASML": 790, "AMD": 140, "ARM": 145
}

# RSI 계산
def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).fillna(0)
    loss = -delta.where(delta < 0, 0).fillna(0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# 종목 분석 함수
def get_stock_signal(ticker):
    try:
        time.sleep(1.2)

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
        max_pain = MAX_PAIN.get(ticker, None)

        if np.isnan(current_ma20) or np.isnan(current_rsi):
            return f"❌ {ticker} 지표 계산 불가"

        message =
