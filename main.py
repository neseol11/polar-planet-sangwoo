import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Streamlit Test",
    page_icon="✅"
)

st.title("✅ Streamlit 연결 테스트")

st.write("이 화면이 보이면 GitHub와 Streamlit이 정상적으로 연결되었습니다.")

st.divider()

st.write("⏰ 현재 시간:")
st.write(datetime.now())

st.caption("페이지를 새로고침하면 시간이 바뀌면 정상입니다.")

st.success("연결 성공!")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io
import numpy as np

# ===============================
# 기본 설정
# ===============================
st.set_page_config(
    page_title="최적의 EC조건은 무엇일까??",
    layout="wide"
)

# ===============================
# 한글 폰트
# ===============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 경로 설정
# ===============================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# ===============================
# 한글 파일명 안전 비교
# ===============================
def norm(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def find_file(directory: Path, target: str):
    for f in directory.iterdir():
        if norm(f.name) == norm(target):
            return f
    return None

# ===============================
# 데이터 로딩
# ===============================
@st.cache_data
def load_env_data():
    if not DATA_DIR.exists():
        st.error("❌ data 폴더가 존재하지 않습니다.")
        st.stop()

    targets = [
        "송도고_환경데이터.csv",
        "하늘고_환경데이터.csv",
        "아라고_환경데이터.csv",
        "동산고_환경데이터.csv",
    ]

    result = {}
    for t in targets:
        f = find_file(DATA_DIR, t)
        if f is None:
            st.error(f"❌ 환경 데이터 파일을 찾을 수 없습니다: {t}")
            st.stop()

        df = pd.read_csv(f)
        df["school"] = t.split("_")[0]
        result[t.split("_")[0]] = df

    return result

@st.cache_data
def load_growth_data():
    f = find_file(DATA_DIR, "4개교_생육결과데이터.xlsx")
    if f is None:
        st.error("❌ 생육 결과 XLSX 파일을 찾을 수 없습니다.")
        st.stop()

    xls = pd.ExcelFile(f, engine="openpyxl")
    frames = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["school"] = sheet
        frames.append(df)

    return pd.concat(frames, ignore_index=True)

# ===============================
# EC 조건
# ===============================
EC_MAP = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

# ===============================
# 데이터 로딩
# ===============================
with st.spinner("📂 데이터 로딩 중..."):
    env_data = load_env_data()
    growth_df = load_growth_data()

growth_df["EC"] = growth_df["school"].map(EC_MAP)

# ===============================
# 사이드바
# ===============================
schools = ["전체"] + list(EC_MAP.keys())
selected_school = st.sidebar.selectbox("🏫 학교 선택", schools)

# ===============================
# 제목
# ===============================
st.title("최적의 EC조건은 무엇일까??")

# ===============================
# Tabs
# ===============================
tab1, tab2, tab3 = st.tabs([
    "📊 EC농도별 생육 결과",
    "📈 간단한 예측 모델",
    "📋 EC-생육 상관관계"
])

# ===============================
# Tab 1
# ===============================
with tab1:
    mean_df = growth_df.groupby("EC").agg({
        "생중량(g)": "mean",
        "잎 수(장)": "mean",
        "지상부 길이(mm)": "mean"
    }).reset_index()

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=["평균 생중량", "평균 잎 수", "평균 지상부 길이"]
    )

    fig.add_bar(x=mean_df["EC"], y=mean_df["생중량(g)"], row=1, col=1)
    fig.add_bar(x=mean_df["EC"], y=mean_df["잎 수(장)"], row=1, col=2)
    fig.add_bar(x=mean_df["EC"], y=mean_df["지상부 길이(mm)"], row=1, col=3)

    fig.add_vline(x=2.0, line_dash="dash", annotation_text="하늘고 EC 2.0 ⭐")

    fig.update_layout(
        height=450,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )

    st.plotly_chart(fig, use_container_width=True)

# ===============================
# Tab 2
# ===============================
with tab2:
    x = growth_df["EC"].values
    y = growth_df["생중량(g)"].values

    coef = np.polyfit(x, y, 2)
    poly = np.poly1d(coef)

    x_range = np.linspace(min(x), max(x), 100)

    fig = go.Figure()
    fig.add_scatter(x=x, y=y, mode="markers", name="실측값")
    fig.add_scatter(x=x_range, y=poly(x_range), mode="lines", name="예측 곡선")

    fig.update_layout(
        xaxis_title="EC",
        yaxis_title="생중량(g)",
        font=dict(family="Malgun Gothic")
    )

    st.plotly_chart(fig, use_container_width=True)

# ===============================
# Tab 3 (🔥 완전 수정)
# ===============================
with tab3:
    corr_df = growth_df[[
        "EC",
        "잎 수(장)",
        "지상부 길이(mm)",
        "지하부길이(mm)",
        "생중량(g)"
    ]].corr()

    fig = go.Figure(
        data=go.Heatmap(
            z=corr_df.values,
            x=corr_df.columns,
            y=corr_df.index,
            colorscale="YlGnBu",
            zmin=-1,
            zmax=1
        )
    )

    fig.update_layout(
        title="EC 및 생육 지표 상관관계",
        font=dict(family="Malgun Gothic")
    )

    st.plotly_chart(fig, use_container_width=True)

    buffer = io.BytesIO()
    corr_df.to_excel(buffer, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        "📥 상관관계 표 XLSX 다운로드",
        data=buffer,
        file_name="EC_생육_상관관계.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



