import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="감독님 투자 엔진", layout="wide")

# 2. 데이터 로드
@st.cache_data(ttl=5)
def load_data(url):
    try:
        # 시트 전체를 읽어옴
        df_raw = pd.read_csv(url)
        # 컬럼명 정리
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        return df_raw
    except:
        return None

sheet_url = "https://docs.google.com/spreadsheets/d/1pbs8DBqbpNfsV-C_Am5Y1PpnfaueepxSTW_lsFCD7w4/export?format=csv"
df = load_data(sheet_url)

if df is not None:
    # --- [데이터 전처리] ---
    # 캡처에 보이는 대로 숫자로 변환 (콤마 제거)
    for col in df.columns:
        if '날짜' not in col:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # 최신 데이터 행 가져오기
    latest_row = df.iloc[0] # 첫 번째 줄에 데이터가 있다고 가정
    last_date = latest_row['날짜']
    
    # 1. 상단 요약 (감독님이 요청한 중간 글씨 포함)
    st.title("🚀 감독님 투자 성장 엔진")
    st.markdown(f"### 📅 기준 일자: {last_date}")
    
    total_assets = latest_row['총 자산']
    target = 350000000
    
    c1, c2, c3 = st.columns(3)
    c1.metric("현재 총 재산액", f"{total_assets:,.0f}원")
    c2.metric("목표 금액", f"{target:,.0f}원")
    c3.metric("남은 금액", f"{max(target - total_assets, 0):,.0f}원")
    
    st.progress(min(max(total_assets/target, 0.0), 1.0), text=f"목표 달성률: {(total_assets/target)*100:.1f}%")
    st.divider()

    # 2. 첫 번째 표: 증권사별 합계 (시트 왼쪽 A~H열 기반)
    st.subheader("📋 증권사별 자산 요약 (원본)")
    asset_cols = ['삼성증권', 'KB증권', '한국투자증권', '업비트', '우리은행', '카카오뱅크']
    summary_data = []
    for col in asset_cols:
        if col in df.columns:
            summary_data.append({"항목": col, "금액": latest_row[col]})
    
    st.table(pd.DataFrame(summary_data).style.format({"금액": "{:,.0f}원"}))
    st.divider()

    # 3. 전체 자산 성장 흐름 그래프
    st.subheader("📉 전체 자산 성장 흐름")
    fig_area = px.area(df, x='날짜', y='총 자산', color_discrete_sequence=['#2E7D32'])
    st.plotly_chart(fig_area, use_container_width=True)
    st.divider()

    # 4. 상세 종목별 수익률 분석 (시트 오른쪽 J~R열 기반)
    st.subheader("📊 상세 종목별 투자 현황")
    # 원금과 평가액 짝 찾기
    detail_items = []
    history_yields = []
    
    # 시트 구조상 원금이 포함된 열들 추출
    orig_cols = [c for c in df.columns if '원금' in c]
    for o_col in orig_cols:
        # 원금 열 바로 다음 열이 평가액임
        idx = df.columns.get_loc(o_col)
        e_col = df.columns[idx+1]
        name = o_col.replace(' 원금', '')
        
        cur_eval = latest_row[e_col]
        cur_orig = latest_row[o_col]
        
        yield_val = ((cur_eval - cur_orig) / cur_orig * 100) if cur_orig != 0 else 0
        detail_items.append({
            "투자 종목": name,
            "현재 평가액": cur_eval,
            "투자 원금": cur_orig,
            "수익률": yield_val
        })
        
        # 그래프용 수익률 계산
        df[f"{name}_수익률"] = ((df[e_col] - df[o_col]) / df[o_col] * 100).fillna(0)
        for _, row in df.iterrows():
            history_yields.append({"날짜": row['날짜'], "종목": name, "수익률(%)": row[f"{name}_수익률"]})

    st.dataframe(pd.DataFrame(detail_items).style.format({
        "현재 평가액": "{:,.0f}원", "투자 원금": "{:,.0f}원", "수익률": "{:.2f}%"
    }), use_container_width=True)
    st.divider()

    # 5. 계좌별 수익률 추이
    st.subheader("📈 상세 종목별 수익률 추이")
    fig_line = px.line(pd.DataFrame(history_yields), x='날짜', y='수익률(%)', color='종목', markers=True)
    fig_line.add_hline(y=0, line_dash="dash", line_color="red")
    st.plotly_chart(fig_line, use_container_width=True)
    st.divider()

    # 6. 자산 포트폴리오 비중
    st.subheader("🍰 증권사별 자산 비중")
    fig_pie = px.pie(pd.DataFrame(summary_data), values='금액', names='항목', hole=0.3)
    st.plotly_chart(fig_pie, use_container_width=True)

    st.success("✅ 할 수 있다!")

else:
    st.error("데이터를 불러오지 못했습니다. 구글 시트의 [공유] 설정이 '링크가 있는 모든 사용자'로 되어 있는지 확인해주세요.")