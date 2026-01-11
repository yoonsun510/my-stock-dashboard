import streamlit as st
import pandas as pd
import plotly.express as px

# --- 스타일 설정 ---
st.markdown("""
    <style>
    .main-title { font-size: 30px !important; font-weight: bold; }
    .date-text { font-size: 18px !important; color: #666; }
    div[data-testid="stMarkdownContainer"] > h3 { font-size: 22px !important; }
    div[data-testid="stMetricLabel"] > div { font-size: 14px !important; }
    div[data-testid="stMetricValue"] > div { font-size: 26px !important; }
    .footer-text { font-size: 20px !important; font-weight: bold; color: #2E7D32; text-align: center; padding: 40px 0px; }
    </style>
    """, unsafe_allow_html=True)

# --- 비밀번호 확인 로직 ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else: st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("비밀번호가 틀렸습니다", type="password", on_change=password_entered, key="password")
        return False
    return True

if check_password():
    st.set_page_config(page_title="감독 투자 엔진", layout="wide")

    @st.cache_data(ttl=5)
    def load_data(url):
        try:
            df_raw = pd.read_csv(url)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            return df_raw
        except: return None

    sheet_url = "https://docs.google.com/spreadsheets/d/1pbs8DBqbpNfsV-C_Am5Y1PpnfaueepxSTW_lsFCD7w4/export?format=csv"
    df = load_data(sheet_url)

    if df is not None:
        for col in df.columns:
            if '날짜' not in col:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        latest_row = df.iloc[0]
        last_date = latest_row['날짜']
        total_assets = latest_row['총 자산']
        target = 350000000

        # 상단 요약
        st.markdown('<p class="main-title">🚀 감독 투자 성장 엔진</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="date-text">📅 기준 일자: {last_date}</p>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("현재 총 재산액", f"{total_assets:,.0f}원")
        c2.metric("목표 금액", f"{target:,.0f}원")
        c3.metric("남은 금액", f"{max(target - total_assets, 0):,.0f}원")
        st.progress(min(max(total_assets/target, 0.0), 1.0))
        st.divider()

        # 데이터 가공 (자산 유형별 합산)
        stock_sum = latest_row.get('삼성증권', 0) + latest_row.get('KB증권', 0) + latest_row.get('한국투자증권', 0)
        coin_sum = latest_row.get('업비트', 0)
        cash_sum = latest_row.get('우리은행', 0) + latest_row.get('카카오뱅크', 0)
        
        type_data = pd.DataFrame({
            "자산유형": ["주식", "코인", "현금"],
            "금액": [stock_sum, coin_sum, cash_sum]
        })

        # --- 신규 그래프: 자산 유형별 비중 ---
        st.subheader("📊 자산 유형별 비중 (주식/코인/현금)")
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig_type = px.pie(type_data, values='금액', names='자산유형', hole=0.4, 
                             color_discrete_map={'주식':'#1f77b4', '코인':'#ff7f0e', '현금':'#2ca02c'})
            st.plotly_chart(fig_type, use_container_width=True)
            
        with col_right:
            # 유형별 금액 표 표시
            st.write("") # 간격 조절
            st.table(type_data.style.format({"금액": "{:,.0f}원"}))
        st.divider()

        # 기존 그래프 및 표들
        st.subheader("📉 전체 자산 성장 흐름")
        st.plotly_chart(px.area(df, x='날짜', y='총 자산', color_discrete_sequence=['#2E7D32']), use_container_width=True)
        
        st.subheader("🍰 증권사별 상세 비중")
        asset_cols = ['삼성증권', 'KB증권', '한국투자증권', '업비트', '우리은행', '카카오뱅크']
        summary_data = [{"항목": col, "금액": latest_row[col]} for col in asset_cols if col in df.columns]
        st.plotly_chart(px.pie(pd.DataFrame(summary_data), values='금액', names='항목', hole=0.3), use_container_width=True)

        # 엔딩 멘트
        st.divider()
        st.markdown('<p class="footer-text">💰 성공적인 투자를 기원합니다, 감독님! 💰</p>', unsafe_allow_html=True)
