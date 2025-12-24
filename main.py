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

# =============================
# 기본 설정
# =============================
st.set_page_config(
    page_title="🌱 극지식물 최적 EC 농도 연구",
    layout="wide"
)

# =============================
# 한글 폰트 깨짐 방지
# =============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# =============================
# 경로 설정 (🔥 핵심 수정)
# =============================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# =============================
# 유틸: 한글 파일명 NFC/NFD 안전 비교
# =============================
def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def find_file(directory: Path, target_name: str):
    target = normalize(target_name)
    for f in directory.iterdir():
        if normalize(f.name) == target:
            return f
    return None

# =============================
# 데이터 로딩
# =============================
@st.cache_data
def load_environment_data():
    if not DATA_DIR.exists():
        st.error("❌ data 폴더를 찾을 수 없습니다. 프로젝트 구조를 확인하세요.")
        st.stop()

    targets = [
        "송도고_환경데이터.csv",
        "하늘고_환경데이터.csv",
        "아라고_환경데이터.csv",
        "동산고_환경데이터.csv",
    ]

    env_data = {}

    for name in targets:
        file = find_file(DATA_DIR, name)
        if file is None:
            st.error(f"❌ 환경 데이터 파일을 찾을 수 없습니다: {name}")
            st.stop()

        df = pd.read_csv(file)
        school = name.split("_")[0]
        df["school"] = school
        env_data[school] = df

    return env_data

@st.cache_data
def load_growth_data():
    file = find_file(DATA_DIR, "4개교_생육결과데이터.xlsx")
    if file is None:
        st.error("❌ 생육 결과 XLSX 파일을 찾을 수 없습니다.")
        st.stop()

    xls = pd.ExcelFile(file, engine="openpyxl")
    frames = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["school"] = sheet
        frames.append(df)

    return pd.concat(frames, ignore_index=True)

# =============================
# EC 조건
# =============================
EC_CONDITIONS = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

# =============================
# 데이터 로딩 UI
# =============================
with st.spinner("📂 데이터를 불러오는 중입니다..."):
    env_data = load_environment_data()
    growth_df = load_growth_data()

# =============================
# 사이드바
# =============================
schools = ["전체"] + list(EC_CONDITIONS.keys())
selected_school = st.sidebar.selectbox("🏫 학교 선택", schools)

# =============================
# 제목
# =============================
st.title("🌱 극지식물 최적 EC 농도 연구")

# =============================
# Tabs
# =============================
tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# =============================
# Tab 1: 실험 개요
# =============================
with tab1:
    st.markdown("""
    ### 🔬 연구 배경 및 목적
    본 연구는 극지식물 생육에 미치는 **EC 농도 영향**을 분석하여  
    최적의 EC 조건을 도출하는 것을 목적으로 한다.
    """)

    overview = pd.DataFrame({
        "학교명": EC_CONDITIONS.keys(),
        "EC 목표": EC_CONDITIONS.values(),
        "개체수": growth_df.groupby("school").size()
    }).reset_index(drop=True)

    st.table(overview)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("총 개체수", f"{len(growth_df)} 개")
    col2.metric("평균 온도", f"{pd.concat(env_data.values())['temperature'].mean():.1f} ℃")
    col3.metric("평균 습도", f"{pd.concat(env_data.values())['humidity'].mean():.1f} %")
    col4.metric("최적 EC", "2.0 (하늘고) ⭐")

# =============================
# Tab 2: 환경 데이터
# =============================
with tab2:
    env_mean = []

    for s, df in env_data.items():
        env_mean.append({
            "학교": s,
            "온도": df["temperature"].mean(),
            "습도": df["humidity"].mean(),
            "pH": df["ph"].mean(),
            "실측 EC": df["ec"].mean(),
            "목표 EC": EC_CONDITIONS[s]
        })

    env_mean_df = pd.DataFrame(env_mean)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    fig.add_bar(x=env_mean_df["학교"], y=env_mean_df["온도"], row=1, col=1)
    fig.add_bar(x=env_mean_df["학교"], y=env_mean_df["습도"], row=1, col=2)
    fig.add_bar(x=env_mean_df["학교"], y=env_mean_df["pH"], row=2, col=1)
    fig.add_bar(x=env_mean_df["학교"], y=env_mean_df["실측 EC"], name="실측 EC", row=2, col=2)
    fig.add_bar(x=env_mean_df["학교"], y=env_mean_df["목표 EC"], name="목표 EC", row=2, col=2)

    fig.update_layout(
        height=700,
        font=dict(family="Malgun Gothic")
    )

    st.plotly_chart(fig, use_container_width=True)

    if selected_school != "전체":
        df = env_data[selected_school]
        fig_ts = px.line(
            df,
            x="time",
            y=["temperature", "humidity", "ec"]
        )
        fig_ts.add_hline(
            y=EC_CONDITIONS[selected_school],
            line_dash="dash",
            annotation_text="목표 EC"
        )
        fig_ts.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig_ts, use_container_width=True)

# =============================
# Tab 3: 생육 결과
# =============================
with tab3:
    growth_df["EC"] = growth_df["school"].map(EC_CONDITIONS)

    mean_weight = growth_df.groupby("EC")["생중량(g)"].mean().reset_index()
    best_ec = mean_weight.loc[mean_weight["생중량(g)"].idxmax(), "EC"]

    fig = px.bar(mean_weight, x="EC", y="생중량(g)")
    fig.add_vline(x=best_ec, line_dash="dash", annotation_text="최적 EC ⭐")
    fig.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig, use_container_width=True)

    fig_box = px.box(growth_df, x="school", y="생중량(g)")
    fig_box.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig_box, use_container_width=True)

    with st.expander("📥 생육 데이터 다운로드"):
        buffer = io.BytesIO()
        growth_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            "XLSX 다운로드",
            data=buffer,
            file_name="생육결과_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


