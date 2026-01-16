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
            # 시트의 모든 데이터를 읽어옴
            df_raw = pd.read_csv(url)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            # 날짜 형식 정리 (시간 제거)
            df_raw['날짜'] = pd.to_datetime(df_raw['날짜']).dt.date
            # 숫자로 변환
            for col in df_raw.columns:
                if col != '날짜' and col != '비고':
                    df_raw[col] = pd.to_numeric(df_raw[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            return df_raw
        except: return None

    sheet_url = "https://docs.google.com/spreadsheets/d/1pbs8DBqbpNfsV-C_Am5Y1PpnfaueepxSTW_lsFCD7w4/export?format=csv"
    df = load_data(sheet_url)

    if df is not None:
        # 중요: 가장 최근 데이터(마지막 행)를 상단 지표에 사용
        latest_row = df.iloc[-1] 
        last_date = latest_row['날짜']
        total_assets = latest_row['총 자산']
        target = 350000000

        # 1. 상단 요약 (최신 데이터 자동 반영)
        st.markdown('<p class="main-title">🚀 감독 투자 성장 엔진</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="date-text">📅 기준 일자: {last_date}</p>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("현재 총 재산액", f"{total_assets:,.0f}원")
        c2.metric("목표 금액", f"{target:,.0f}원")
        c3.metric("남은 금액", f"{max(target - total_assets, 0):,.0f}원")
        st.progress(min(max(total_assets/target, 0.0), 1.0))
        st.divider()

        # 2. 자산 유형별 비중
        st.subheader("📊 자산 유형별 비중 (주식/코인/현금)")
        stock_sum = latest_row.get('삼성증권', 0) + latest_row.get('KB증권', 0) + latest_row.get('한국투자증권', 0)
        coin_sum = latest_row.get('업비트', 0)
        cash_sum = latest_row.get('우리은행', 0) + latest_row.get('카카오뱅크', 0)
        type_df = pd.DataFrame({"자산유형": ["주식", "코인", "현금"], "금액": [stock_sum, coin_sum, cash_sum]})
        
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.plotly_chart(px.pie(type_df, values='금액', names='자산유형', hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe), use_container_width=True)
        with col_b:
            st.table(type_df.style.format({"금액": "{:,.0f}원"}))
        st.divider()

        # 3. 증권사별 자산 요약 (최신 데이터 반영)
        st.subheader("📋 증권사별 자산 요약")
        asset_cols = ['삼성증권', 'KB증권', '한국투자증권', '업비트', '우리은행', '카카오뱅크']
        summary_data = [{"항목": col, "금액": latest_row[col]} for col in asset_cols if col in df.columns]
        st.table(pd.DataFrame(summary_data).style.format({"금액": "{:,.0f}원"}))

        # 4. 전체 자산 성장 흐름 (날짜만 표시 + 가로 이동 제한)
        st.subheader("📉 전체 자산 성장 흐름")
        fig_area = px.area(df, x='날짜', y='총 자산', color_discrete_sequence=['#2E7D32'])
        fig_area.update_xaxes(type='category') # 날짜를 간격별로 고정 (시간 단위 제거)
        fig_area.update_layout(dragmode='pan', yaxis_fixedrange=True) # 위아래 고정, 가로 이동(pan)만 허용
        st.plotly_chart(fig_area, use_container_width=True)

        # 5. 상세 종목별 투자 현황 (최신 데이터 반영)
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
            
            # 수익률 추이 그래프 데이터
            temp_df = df[['날짜', o_col, e_col]].copy()
            temp_df['종목'] = name
            temp_df['수익률(%)'] = ((temp_df[e_col] - temp_df[o_col]) / temp_df[o_col] * 100).fillna(0)
            history_yields.append(temp_df)
        
        st.dataframe(pd.DataFrame(detail_items).style.format({"평가액": "{:,.0f}원", "원금": "{:,.0f}원", "수익률": "{:.2f}%"}), use_container_width=True)

        # 6. 상세 종목별 수익률 추이 (날짜 고정)
        st.subheader("📈 상세 종목별 수익률 추이")
        if history_yields:
            all_history = pd.concat(history_yields)
            fig_line = px.line(all_history, x='날짜', y='수익률(%)', color='종목', markers=True)
            fig_line.update_xaxes(type='category')
            fig_line.update_layout(dragmode='pan', yaxis_fixedrange=True)
            st.plotly_chart(fig_line, use_container_width=True)

        # 7. 증권사별 자산 비중
        st.subheader("🍰 증권사별 자산 비중")
        st.plotly_chart(px.pie(pd.DataFrame(summary_data), values='금액', names='항목', hole=0.3), use_container_width=True)

        st.divider()
        st.markdown('<p class="footer-text">💰 성공적인 투자를 기원합니다, 감독님! 💰</p>', unsafe_allow_html=True)
