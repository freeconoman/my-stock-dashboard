import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 필수 데이터 함수 정의
@st.cache_data
def get_technical_data(ticker):
    df = yf.download(ticker, period="10y")
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 지표 계산
    df['SMA5'] = df['Close'].rolling(5).mean()
    df['SMA10'] = df['Close'].rolling(10).mean()
    df['SMA20'] = df['Close'].rolling(20).mean()
    
    # 일목균형표 핵심 지표
    high_9 = df['High'].rolling(9).max()
    low_9 = df['Low'].rolling(9).min()
    df['Conversion'] = (high_9 + low_9) / 2
    
    # 전략별 지표 계산
    df['TRIX'] = df['Close'].ewm(span=9).mean().pct_change()
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).cumsum()
    
    return df.dropna()

# 2. 전략 계산 엔진
def calculate_strategies(df):
    df['S1'] = np.where(df['TRIX'] > 0, 1, 0)
    df['S2'] = np.where(df['Close'] > df['Close'].shift(26), 1, 0)
    df['S3'] = np.where(df['Close'] > df['Close'].rolling(26).mean(), 1, 0)
    df['S4'] = np.where((df['Conversion'] > df['SMA10']), 1, 0)
    df['S5'] = np.where((df['Close'] > df['Close'].rolling(60).max().shift(1)), 1, 0)
    return df

# 3. 백테스트 엔진
def get_backtest_stats(df, signal_col, years):
    subset = df.last(f'{years}Y')
    returns = subset['Close'].pct_change()
    strat_ret = subset[signal_col].shift(1) * returns
    win_rate = (strat_ret > 0).mean() * 100
    cum_ret = (1 + strat_ret).prod() - 1
    pos = strat_ret[strat_ret > 0].mean()
    neg = abs(strat_ret[strat_ret < 0].mean())
    pl_ratio = pos / neg if neg != 0 else 0
    return win_rate, pl_ratio, cum_ret

# 4. 메인 대시보드
st.title("📊 통합 매매기법 분석 플랫폼")
ticker = st.text_input("종목코드 (예: 005930.KS)", "005930.KS")

if st.button("분석 실행"):
    df = get_technical_data(ticker)
    if df is not None:
        df = calculate_strategies(df)
        strategies = {"1. TRIX": "S1", "2. 후행스팬": "S2", "3. 선행스팬": "S3", "4. 꿀단타": "S4", "5. MACD/OBV": "S5"}
        
        for name, col in strategies.items():
            st.subheader(f"💡 {name}")
            wr3, pl3, cr3 = get_backtest_stats(df, col, 3)
            wr5, pl5, cr5 = get_backtest_stats(df, col, 5)
            wr10, pl10, cr10 = get_backtest_stats(df, col, 10)
            
            data = {"기간": ["3개년", "5개년", "10개년"], 
                    "승률(%)": [f"{wr3:.1f}", f"{wr5:.1f}", f"{wr10:.1f}"],
                    "손익비": [f"{pl3:.2f}", f"{pl5:.2f}", f"{pl10:.2f}"],
                    "누적수익(%)": [f"{cr3*100:.1f}", f"{cr5*100:.1f}", f"{cr10*100:.1f}"]}
            st.table(pd.DataFrame(data))
    else:
        st.error("데이터를 가져올 수 없습니다. 종목코드를 다시 확인하세요.")
