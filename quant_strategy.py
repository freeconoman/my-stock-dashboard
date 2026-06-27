import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 데이터 로드 및 지표 생성 함수
def get_technical_data(ticker):
    # 데이터를 충분히 길게 가져옵니다
    df = yf.download(ticker, period="1y")
    
    # 데이터가 비어있으면 에러 방지
    if df.empty:
        return None

    # 데이터 타입이 다중 인덱스일 경우 단일 인덱스로 변경 (yfinance 버전 이슈 방지)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 지표 계산 전 결측치나 형태 확인
    df['SMA10'] = df['Close'].rolling(10).mean()
    
    # 1. TRIX 계산 (지수이동평균의 변화율)
    ema = df['Close'].ewm(span=9, adjust=False).mean()
    df['TRIX'] = (ema - ema.shift(1)) / ema.shift(1)
    
    # 2. 일목균형표 전환선 계산
    high_9 = df['High'].rolling(9).max()
    low_9 = df['Low'].rolling(9).min()
    df['Conversion'] = (high_9 + low_9) / 2
    
    # 3. 선행스팬 A 계산
    # .rolling(26).mean() 결과와 Conversion을 더할 때 형식을 맞춤
    df['Span_A'] = (df['Conversion'] + df['Close'].rolling(26).mean()) / 2
    
    # 4. 거래량 OBV
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).cumsum()
    
    # 마지막에 결측치(데이터가 없는 처음 부분)를 제거하여 에러 방지
    return df.dropna()

# 전략 엔진
def get_signals(df):
    signals = {}
    last = df.iloc[-1]
    
    # 전략 1: TRIX & Stoch (간소화)
    signals['전략1'] = "매수 대기" if last['TRIX'] > 0 else "관망"
    # 전략 2: 후행스팬 (주가와 26일 차이)
    signals['전략2'] = "강력 매수" if last['Close'] > df['Close'].shift(26).iloc[-1] else "관망"
    # 전략 4: 꿀단타
    if last['Conversion'] > last['SMA10']:
        signals['전략4'] = "단기 슈팅 구간"
    else:
        signals['전략4'] = "관망"
    return signals

# 대시보드 UI
st.title("📈 5대 매매기법 통합 엔진")
ticker = st.text_input("종목코드 입력 (예: 005930.KS)", "005930.KS")

if st.button("실시간 전략 분석"):
    df = get_technical_data(ticker)
    signals = get_signals(df)
    
    for strategy, status in signals.items():
        st.subheader(f"💡 {strategy}")
        if "매수" in status:
            st.success(f"상태: {status}")
        else:
            st.warning(f"상태: {status}")
