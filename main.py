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
from pathlib import Path
import unicodedata
import io
import numpy as np

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ------------------------
# 기본 설정
# ------------------------
st.set_page_config(
    page_title="EC농도별 생육결과",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

SCHOOL_EC = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

# ------------------------
# 파일 탐색 유틸
# ------------------------
def normalize(text):
    return unicodedata.normalize("NFC", text)

def find_file_by_name(directory: Path, target_name: str):
    target_norm = normalize(target_name)
    for file in directory.iterdir():
        if normalize(file.name) == target_norm:
            return file
    return None

# ------------------------
# 데이터 로딩
# ------------------------
@st.cache_data
def load_environment_data():
    env_data = {}
    with st.spinner("환경 데이터 로딩 중..."):
        for school in SCHOOL_EC.keys():
            filename = f"{school}_환경데이터.csv"
            file_path = find_file_by_name(DATA_DIR, filename)
            if file_path is None:
                st.error(f"❌ 환경 데이터 파일을 찾을 수 없습니다: {filename}")
                continue
            df = pd.read_csv(file_path)
            df["학교"] = school
            df["ec_조건"] = SCHOOL_EC[school]
            env_data[school] = df
    return env_data

@st.cache_data
def load_growth_data():
    xlsx_path = find_file_by_name(DATA_DIR, "4개교_생육결과데이터.xlsx")
    if xlsx_path is None:
        st.error("❌ 생육 결과 XLSX 파일을 찾을 수 없습니다.")
        return {}

    with st.spinner("생육 결과 데이터 로딩 중..."):
        xls = pd.ExcelFile(xlsx_path, engine="openpyxl")
        growth = {}
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            df["학교"] = sheet
            df["ec_조건"] = SCHOOL_EC.get(sheet, np.nan)
            growth[sheet] = df
    return growth

env_data = load_environment_data()
growth_data = load_growth_data()

if not growth_data:
    st.stop()

# ------------------------
# 사이드바
# ------------------------
st.sidebar.title("학교 선택")
school_option = st.sidebar.selectbox(
    "학교",
    ["전체"] + list(SCHOOL_EC.keys())
)

# ------------------------
# 데이터 통합
# ------------------------
all_growth_df = pd.concat(growth_data.values(), ignore_index=True)

if school_option != "전체":
    all_growth_df = all_growth_df[all_growth_df["학교"] == school_option]

# ------------------------
# 메인 UI
# ------------------------
st.title("🌱 EC농도별 생육결과")

tab1, tab2, tab3 = st.tabs([
    "📊 EC농도별 생육 결과",
    "📈 간단한 예측 모델",
    "📋 EC-생육 상관관계"
])

# ========================
# TAB 1
# ========================
with tab1:
    st.subheader("EC 농도별 생중량 비교")

    fig = px.box(
        all_growth_df,
        x="ec_조건",
        y="생중량(g)",
        color="학교",
        points="all",
        labels={"ec_조건": "EC 농도", "생중량(g)": "생중량(g)"}
    )

    fig.add_vrect(
        x0=1.2, x1=1.3,
        fillcolor="green",
        opacity=0.2,
        annotation_text="최적 EC 범위",
        annotation_position="top left"
    )

    fig.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )

    st.plotly_chart(fig, use_container_width=True)

# ========================
# TAB 2
# ========================
with tab2:
    st.subheader("EC 농도 기반 생중량 예측 (단순 회귀)")

    df = all_growth_df.dropna(subset=["ec_조건", "생중량(g)"])
    X = df["ec_조건"].values
    y = df["생중량(g)"].values

    coef = np.polyfit(X, y, 1)
    poly = np.poly1d(coef)

    x_line = np.linspace(X.min(), X.max(), 100)
    y_line = poly(x_line)

    fig = go.Figure()
    fig.add_scatter(x=X, y=y, mode="markers", name="실제 데이터")
    fig.add_scatter(x=x_line, y=y_line, mode="lines", name="예측 선형 모델")

    fig.update_layout(
        xaxis_title="EC 농도",
        yaxis_title="생중량(g)",
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "⚠ 데이터 수가 4개 조건뿐이므로 모델 신뢰도는 낮습니다.\n"
        "온도·습도·pH 등 다른 환경 요인의 영향이 큽니다."
    )

# ========================
# TAB 3
# ========================
with tab3:
    st.subheader("EC와 생육 지표 간 상관관계")

    corr_df = all_growth_df[
        ["ec_조건", "잎 수(장)", "지상부 길이(mm)", "지하부길이(mm)", "생중량(g)"]
    ].corr().round(3)

    st.dataframe(corr_df, use_container_width=True)

    buffer = io.BytesIO()
    corr_df.to_excel(buffer, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        label="📥 상관관계 결과 다운로드 (XLSX)",
        data=buffer,
        file_name="EC_생육_상관관계.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )




