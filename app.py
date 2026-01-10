import streamlit as st
import pandas as pd
import plotly.express as px

# --- 스타일 설정 (폰트 크기 및 마지막 멘트 스타일) ---
st.markdown("""
    <style>
    .main-title { font-size: 30px !important; font-weight: bold; }
    .date-text { font-size: 18px !important; color: #666; }
    div[data-testid="stMarkdownContainer"] > h3 { font-size: 22px !important; }
    div[data-testid="stMetricLabel"] > div { font-size: 14px !important; }
    div[data-testid="stMetricValue"] > div { font-size: 26px !important; }
    /* 마지막 멘트 스타일 */
    .footer-text { 
        font-size: 20px !important; 
        font-weight: bold; 
        color: #2E7D32; 
        text-align: center; 
        padding: 40px 0px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 비밀번호 확인 로직 ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("비밀번호가 틀렸습니다", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

if check_password():
    # 1. 페이지 설정 (이름도 '감독'으로 변경)
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

        # --- 화면 구성 시작 ---
        st.markdown('<p class="main-title">🚀 감독 투자 성장 엔진</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="date-text">📅 기준 일자: {last_date}</p>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("현재 총 재산액", f"{total_assets:,.0f}원")
        c2.metric("목표 금액", f"{target:,.0f}원")
        c3.metric("남은 금액", f"{max(target - total_assets, 0):,.0f}원")
        st.progress(min(max(total_assets/target, 0.0), 1.0))
        st.divider()

        st.subheader("📋 증권사별 자산 요약")
        asset_cols = ['삼성증권', 'KB증권', '한국투자증권', '업비트', '우리은행', '카카오뱅크']
        summary_data = [{"항목": col, "금액": latest_row[col]} for col in asset_cols if col in df.columns]
        st.table(pd.DataFrame(summary_data).style.format({"금액": "{:,.0f}원"}))

        st.subheader("📉 전체 자산 성장 흐름")
        st.plotly_chart(px.area(df, x='날짜', y='총 자산', color_discrete_sequence=['#2E7D32']), use_container_width=True)

        st.subheader("📊 상세 종목별 투자 현황")
        orig_cols = [c for c in df.columns if '원금' in c]
        detail_items = []
        history_yields = []
        for o_col in orig_cols:
            idx = df.columns.get_loc(o_col)
            e_col = df.columns[idx+1]
            name = o_col.replace(' 원금', '')
            cur_eval, cur_orig = latest_row[e_col], latest_row[o_col]
            detail_items.append({"종목": name, "평가액": cur_eval, "원금": cur_orig, "수익률": ((cur_eval-cur_orig)/cur_orig*100) if cur_orig!=0 else 0})
            df[f"{name}_y"] = ((df[e_col]-df[o_col])/df[o_col]*100).fillna(0)
            for _, row in df.iterrows():
                history_yields.append({"날짜": row['날짜'], "종목": name, "수익률(%)": row[f"{name}_y"]})
        
        st.dataframe(pd.DataFrame(detail_items).style.format({"평가액": "{:,.0f}원", "원금": "{:,.0f}원", "수익률": "{:.2f}%"}), use_container_width=True)

        st.subheader("📈 상세 종목별 수익률 추이")
        st.plotly_chart(px.line(pd.DataFrame(history_yields), x='날짜', y='수익률(%)', color='종목', markers=True), use_container_width=True)

        st.subheader("🍰 증권사별 자산 비중")
        st.plotly_chart(px.pie(pd.DataFrame(summary_data), values='금액', names='항목', hole=0.3), use_container_width=True)

        # --- 마지막 멘트 (요청하신 부분) ---
        st.divider()
        st.markdown('<p class="footer-text">💰 성공적인 투자로 애니 회사를 차리시는 그날까지 화이팅하세요, 감독님! 💰</p>', unsafe_allow_html=True)
