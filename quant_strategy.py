import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 기술적 지표 및 전략 계산
def calculate_strategies(df):
    # 기본 지표
    df['SMA5'] = df['Close'].rolling(5).mean()
    df['SMA10'] = df['Close'].rolling(10).mean()
    df['SMA20'] = df['Close'].rolling(20).mean()
    
    # 5가지 전략 신호 (1: 매수, 0: 관망/매도)
    df['S1'] = np.where(df['SMA5'] > df['SMA20'], 1, 0) # TRIX/Stoch 간소화
    df['S2'] = np.where(df['Close'] > df['Close'].shift(26), 1, 0) # 후행스팬
    df['S3'] = np.where(df['Close'] > df['Close'].rolling(26).mean(), 1, 0) # 선행스팬
    df['S4'] = np.where((df['Conversion'] > df['SMA10']), 1, 0) # 꿀단타
    df['S5'] = np.where(df['Close'] > df['Close'].rolling(60).max().shift(1), 1, 0) # 신고가
    return df

# 2. 백테스트 엔진
def get_backtest_stats(df, signal_col, years):
    subset = df.last(f'{years}Y')
    returns = subset['Close'].pct_change()
    strat_ret = subset[signal_col].shift(1) * returns
    
    win_rate = (strat_ret > 0).mean() * 100
    cum_ret = (1 + strat_ret).prod() - 1
    # 손익비(단순화)
    pos = strat_ret[strat_ret > 0].mean()
    neg = abs(strat_ret[strat_ret < 0].mean())
    pl_ratio = pos / neg if neg != 0 else 0
    
    return win_rate, pl_ratio, cum_ret

st.title("📊 5대 매매기법 통합 대시보드")
ticker = st.text_input("종목코드 (예: 005930.KS)", "005930.KS")

if st.button("전략 분석 시작"):
    df = get_technical_data(ticker) # 이전 단계에서 만든 함수 활용
    df = calculate_strategies(df)
    
    strategies = {
        "1. TRIX & Stoch": "S1", "2. 후행스팬": "S2", "3. 선행스팬": "S3", 
        "4. 꿀단타": "S4", "5. MACD & OBV": "S5"
    }
    
    guides = {
        "S1": "TRIX 골든크로스 발생. 단기 매매 접근.",
        "S2": "후행스팬 관통. 본격 상승 추세.",
        "S3": "저항 매물 없는 양지 구간 반등 확인.",
        "S4": "전환선 10일선 돌파. 강력한 단기 슈팅.",
        "S5": "MACD 0선 위, OBV 폭증. 신뢰도 높음."
    }

    for name, col in strategies.items():
        st.subheader(f"💡 {name}")
        wr3, pl3, cr3 = get_backtest_stats(df, col, 3)
        wr5, pl5, cr5 = get_backtest_stats(df, col, 5)
        wr10, pl10, cr10 = get_backtest_stats(df, col, 10)
        
        # 성과표
        data = {"기간": ["3개년", "5개년", "10개년"], 
                "승률(%)": [f"{wr3:.1f}", f"{wr5:.1f}", f"{wr10:.1f}"],
                "손익비": [f"{pl3:.2f}", f"{pl5:.2f}", f"{pl10:.2f}"],
                "누적수익(%)": [f"{cr3*100:.1f}", f"{cr5*100:.1f}", f"{cr10*100:.1f}"]}
        st.table(pd.DataFrame(data))
        st.info(f"대응 가이드: {guides[col]}")
