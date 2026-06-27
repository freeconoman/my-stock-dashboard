import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 대응 가이드 (키 값을 name 변수와 완벽하게 일치시킴)
STRATEGY_DETAILS = {
    "1. TRIX & Stoch": {"근거": "TRIX 방향성 전환", "대응": "골든크로스 시 분할 매수, 데드크로스 발생 시 추격 매도"},
    "2. 후행스팬": {"근거": "주가 상대 위치", "대응": "관통 시 추격 매수, 하향 이탈 시 전략 매도"},
    "3. 선행스팬": {"근거": "매물대 두께", "대응": "구름대 반등 시 눌림목 매수, 신저가 갱신 시 분할 손절"},
    "4. 꿀단타": {"근거": "단기 슈팅 시그널", "대응": "돌파 시 추격 매수, 과열권 진입 시 전략 매도"},
    "5. MACD/OBV": {"근거": "거래량 동반 추세", "대응": "0선 위 돌파 시 유지, 거래량 이탈 시 분할 매도"}
}

def get_technical_data(ticker):
    df = yf.download(ticker, period="10y")
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    df['SMA10'] = df['Close'].rolling(10).mean()
    high_9 = df['High'].rolling(9).max()
    low_9 = df['Low'].rolling(9).min()
    df['Conversion'] = (high_9 + low_9) / 2
    df['TRIX'] = df['Close'].ewm(span=9).mean().pct_change()
    return df.dropna()

def get_backtest_stats(df, signal_col, period_type):
    if period_type == "22.01-25.03":
        subset = df.loc['2022-01-01':'2025-03-31']
    else:
        years = int(period_type.replace('개년', ''))
        start_date = df.index[-1] - pd.DateOffset(years=years)
        subset = df.loc[start_date:]
    
    returns = subset['Close'].pct_change()
    strat_ret = subset[signal_col].shift(1) * returns
    win_rate = (strat_ret > 0).mean() * 100
    cum_ret = (1 + strat_ret).prod() - 1
    pos = strat_ret[strat_ret > 0].mean()
    neg = abs(strat_ret[strat_ret < 0].mean())
    pl_ratio = pos / neg if (neg != 0 and not np.isnan(neg)) else 0
    return win_rate, pl_ratio, cum_ret

st.title("📈 고도화된 매매기법 분석 플랫폼")
ticker = st.text_input("종목코드 (예: 005930.KS)", "005930.KS")

if st.button("분석 실행"):
    df = get_technical_data(ticker)
    if df is not None:
        df['S1'], df['S2'], df['S3'] = np.where(df['TRIX']>0,1,0), np.where(df['Close']>df['Close'].shift(26),1,0), np.where(df['Close']>df['Close'].rolling(26).mean(),1,0)
        df['S4'], df['S5'] = np.where(df['Conversion']>df['SMA10'],1,0), np.where(df['Close']>df['Close'].rolling(60).max().shift(1),1,0)
        
        # 키값 이름 일치
        strategy_map = {
            "1. TRIX & Stoch": "S1", "2. 후행스팬": "S2", 
            "3. 선행스팬": "S3", "4. 꿀단타": "S4", "5. MACD/OBV": "S5"
        }
        
        for name, key in strategy_map.items():
            st.subheader(f"💡 {name}")
            periods = ["3개년", "5개년", "10개년", "22.01-25.03"]
            stats = [get_backtest_stats(df, key, p) for p in periods]
            
            data = {"기간": periods, "승률(%)": [f"{s[0]:.1f}" for s in stats], "손익비": [f"{s[1]:.2f}" for s in stats], "누적수익(%)": [f"{s[2]*100:.1f}" for s in stats]}
            st.table(pd.DataFrame(data))
            st.warning(f"**상세 대응:** {STRATEGY_DETAILS[name]['대응']} (근거: {STRATEGY_DETAILS[name]['근거']})")
    else:
        st.error("데이터를 가져올 수 없습니다.")
