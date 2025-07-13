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

        if np.isnan(current_ma20) or np.isnan(current_rsi):
            return f"❌ {ticker} 지표 계산 불가"

        # ✅ Max Pain
        MAX_PAIN = {
            "TSLA": 310, "ORCL": 225, "MSFT": 490, "AMZN": 215, "NVDA": 160,
            "META": 700, "AAPL": 200, "AVGO": 265, "GOOGL": 177.5, "PSTG": 55,
            "SYM": 43, "TSM": 225, "ASML": 790, "AMD": 140, "ARM": 145
        }
        max_pain = MAX_PAIN.get(ticker, "N/A")

        # 🧠 메시지 시작
        message = f"\n\n📈 {ticker}\n종가: ${current_close:.2f} / MA20: ${current_ma20:.2f} / RSI: {current_rsi:.2f} / MaxPain: ${max_pain}"

        # 🧪 조건 판단 (RSI 우선)
        if current_rsi > 65:
            message += "\n🔴 RSI>65 → 매도 경고"
        elif current_rsi < 40:
            message += "\n🟢 RSI<40 → 매수 기회"
        elif current_close > current_ma20:
            message += "\n🟢 MA20 돌파 → 상승 추세"
        elif current_close < current_ma20:
            message += "\n🔴 MA20 이탈 → 하락 추세"
        else:
            message += "\n❓ 관망각"

        # ⚠️ Max Pain 분석
        if isinstance(max_pain, (int, float)):
            if current_close > max_pain * 1.03:
                message += "\n⚠️ Max Pain 상단 이탈 → 매도 압력 경계"
            elif current_close < max_pain * 0.97:
                message += "\n⚠️ Max Pain 하단 이탈 → 반등 기대 영역"

        return message
    except Exception as e:
        return f"❌ {ticker} 처리 중 에러: {str(e)}"
