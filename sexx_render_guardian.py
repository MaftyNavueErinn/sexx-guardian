import time
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask
from datetime import datetime
import logging
import requests

app = Flask(__name__)

TICKERS = [
    "TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL",
    "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"
]

RSI_THRESHOLD = 40

# Max Pain 수동 등록
MAX_PAIN = {
    "TSLA": 310,
    "ORCL": 225,
    "MSFT": 490,
    "AMZN": 215,
    "NVDA": 160,
    "META": 700,
    "AAPL": 200,
    "AVGO": 265,
    "GOOGL": 177.5,
    "PSTG": 55,
    "SYM": 43,
    "TSM": 225,
    "ASML": 790,
    "AMD": 140,
    "ARM": 145
}

# 텔레그램 알림 설정
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ/sendMessage"
    payload = {"chat_id": "7733010521", "text": text}
    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            print(f"❌ 텔레그램 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 텔레그램 전송 에러: {e}")

def get_rsi(close_prices, period=14):
    delta = close_prices.diff()
    up = delta.clip(lower=0)
