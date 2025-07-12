import os

# Create the modified Python script content with the provided API and Telegram credentials
script_content = f"""
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import datetime
from pytz import timezone
from ta.momentum import RSIIndicator
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler

# Telegram API
TG_TOKEN = "7641333408:AAFe0wDhUZnALhVuoWosu0GFdDgDqXi3yGQ"
TG_CHAT_ID = "7733010521"
bot = Bot(token=TG_TOKEN)

# 감시할 종목들
tickers = ["TSLA", "ORCL", "MSFT", "AMZN", "NVDA", "META", "AAPL", "AVGO", "GOOGL", "PSTG", "SYM", "TSM", "ASML", "AMD", "ARM"]

# 트리거 기준
RSI_THRESHOLD = 40

def fetch_stock_data(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1d", progress=False)
        df.dropna(inplace=True)
        df["RSI"] = RSIIndicator(close=df["Close"]).rsi()
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["MA60"] = df["Close"].rolling(window=60).mean()
        return df
    except Exception as e:
        return str(e)

def analyze_and_alert():
    for ticker in tickers:
        try:
            df = fetch_stock_data(ticker)
            if isinstance(df, str):
                bot.send_message(chat_id=TG_CHAT_ID, text=f"❌ 분석 실패: {ticker}\\n에러: {df}")
                continue

            rsi_latest = df["RSI"].iloc[-1]
            close_latest = df["Close"].iloc[-1]
            ma20_latest = df["MA20"].iloc[-1]

            condition_rsi = rsi_latest < RSI_THRESHOLD
            condition_ma20_cross = close_latest > ma20_latest

            if condition_rsi or condition_ma20_cross:
                msg = f"🚨 [{ticker}] 트리거 감지됨\\n종가: {close_latest:.2f}\\nRSI: {rsi_latest:.2f}\\nMA20: {ma20_latest:.2f}"
                bot.send_message(chat_id=TG_CHAT_ID, text=msg)
        except Exception as e:
            bot.send_message(chat_id=TG_CHAT_ID, text=f"❌ 분석 실패: {ticker}\\n에러: {str(e)}")

# 스케줄러 실행
scheduler = BlockingScheduler(timezone=timezone("Asia/Seoul"))
scheduler.add_job(analyze_and_alert, 'interval', hours=1)
scheduler.start()
"""

# Save the script as a .py file
file_path = "/mnt/data/sexx_render_guardian.py"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(script_content)

file_path
