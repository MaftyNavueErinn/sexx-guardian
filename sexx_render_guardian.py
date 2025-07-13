# ✅ 알림 체크 함수 (수정 완료)
def check_alerts():
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="21d", interval="1d", progress=False, auto_adjust=True)
            if df.empty:
                continue

            df.dropna(inplace=True)
            close = df["Close"]
            volume = df["Volume"]
            rsi_series = get_rsi(close)

            if rsi_series.isna().iloc[-1]:
                continue

            # ✅ float() 강제 변환 (여기가 핵심)
            price = float(close.iloc[-1])
            ma20 = float(close.rolling(20).mean().iloc[-1])
            volume_today = float(volume.iloc[-1])
            volume_ma5 = float(volume.rolling(5).mean().iloc[-1])
            rsi = float(rsi_series.iloc[-1])

            alerts = []

            if rsi < RSI_LOW:
                alerts.append(f"⚠️ RSI 과매도 ({rsi:.2f})")
            elif rsi > RSI_HIGH:
                alerts.append(f"🚨 RSI 과매수 ({rsi:.2f})")

            if price > ma20:
                alerts.append(f"📈 MA20 돌파 (${ma20:.2f})")
            elif price < ma20:
                alerts.append(f"📉 MA20 이탈 (${ma20:.2f})")

            max_pain = MAX_PAIN.get(ticker)
            if max_pain:
                gap_percent = abs(price - max_pain) / max_pain * 100
                if gap_percent >= 5:
                    alerts.append(f"💀 체산각: MaxPain ${max_pain:.2f} / 현재가 ${price:.2f}")

            if volume_today > volume_ma5 * 2:
                alerts.append(f"🔥 거래량 급등: {volume_today:,.0f} / 평균 {volume_ma5:,.0f}")

            if alerts:
                msg = f"🔍 [{ticker}] 감지됨\n" + "\n".join(alerts)
                send_telegram_message(msg)

        except Exception as e:
            print(f"❌ {ticker} 오류: {e}")
