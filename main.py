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
# 한글 폰트 깨짐 방지 (CSS)
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
# 유틸: 한글 파일명 안전 비교
# =============================
def normalize_name(name: str):
    return unicodedata.normalize("NFC", name)

def find_file_by_normalized_name(directory: Path, target_name: str):
    target_norm = normalize_name(target_name)
    for f in directory.iterdir():
        if normalize_name(f.name) == target_norm:
            return f
    return None

# =============================
# 데이터 로딩
# =============================
@st.cache_data
def load_environment_data():
    data_dir = Path("data")
    env_files = {}
    targets = [
        "송도고_환경데이터.csv",
        "하늘고_환경데이터.csv",
        "아라고_환경데이터.csv",
        "동산고_환경데이터.csv",
    ]

    for t in targets:
        f = find_file_by_normalized_name(data_dir, t)
        if f is None:
            st.error(f"❌ 환경 데이터 파일을 찾을 수 없습니다: {t}")
            return None
        df = pd.read_csv(f)
        df["school"] = t.split("_")[0]
        env_files[t.split("_")[0]] = df

    return env_files

@st.cache_data
def load_growth_data():
    data_dir = Path("data")
    xlsx_name = "4개교_생육결과데이터.xlsx"
    f = find_file_by_normalized_name(data_dir, xlsx_name)
    if f is None:
        st.error("❌ 생육 결과 XLSX 파일을 찾을 수 없습니다.")
        return None

    xls = pd.ExcelFile(f, engine="openpyxl")
    data = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["school"] = sheet
        data.append(df)

    return pd.concat(data, ignore_index=True)

# =============================
# EC 조건 정의
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
with st.spinner("데이터를 불러오는 중입니다..."):
    env_data = load_environment_data()
    growth_df = load_growth_data()

if env_data is None or growth_df is None:
    st.stop()

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
    st.subheader("🔬 연구 배경 및 목적")
    st.markdown("""
    본 연구는 **극지식물의 생육에 최적화된 EC 농도**를 도출하기 위해  
    4개 고등학교에서 서로 다른 EC 조건 하에서 생육 실험을 수행하고  
    환경 요인과 생육 결과의 상관관계를 분석하였다.
    """)

    overview_df = pd.DataFrame({
        "학교명": EC_CONDITIONS.keys(),
        "EC 목표": EC_CONDITIONS.values(),
        "개체수": growth_df.groupby("school").size().values,
    })
    st.table(overview_df)

    total_count = len(growth_df)
    avg_temp = pd.concat(env_data.values())["temperature"].mean()
    avg_hum = pd.concat(env_data.values())["humidity"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 개체수", f"{total_count} 개")
    col2.metric("평균 온도", f"{avg_temp:.1f} ℃")
    col3.metric("평균 습도", f"{avg_hum:.1f} %")
    col4.metric("최적 EC", "2.0 (하늘고) ⭐")

# =============================
# Tab 2: 환경 데이터
# =============================
with tab2:
    st.subheader("📊 학교별 환경 평균 비교")

    env_mean = []
    for s, df in env_data.items():
        env_mean.append({
            "학교": s,
            "temperature": df["temperature"].mean(),
            "humidity": df["humidity"].mean(),
            "ph": df["ph"].mean(),
            "ec": df["ec"].mean(),
            "target_ec": EC_CONDITIONS[s]
        })
    env_mean_df = pd.DataFrame(env_mean)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    fig.add_bar(x=env_mean_df["학교"], y=env_mean_df["temperature"], row=1, col=1)
    fig.add_bar(x=env_mean_df["학교"], y=env_mean_df["humidity"], row=1, col=2)
    fig.add_bar(x=env_mean_df["학교"], y=env_mean_df["ph"], row=2, col=1)

    fig.add_bar(x=env_mean_df["학교"], y=env_mean_df["ec"], name="실측 EC", row=2, col=2)
    fig.add_bar(x=env_mean_df["학교"], y=env_mean_df["target_ec"], name="목표 EC", row=2, col=2)

    fig.update_layout(
        height=700,
        showlegend=True,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )

    st.plotly_chart(fig, use_container_width=True)

    if selected_school != "전체":
        st.subheader(f"📈 {selected_school} 환경 시계열")
        df = env_data[selected_school]

        fig2 = px.line(
            df,
            x="time",
            y=["temperature", "humidity", "ec"],
            labels={"value": "값", "variable": "항목"}
        )
        fig2.add_hline(
            y=EC_CONDITIONS[selected_school],
            line_dash="dash",
            annotation_text="목표 EC"
        )
        fig2.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📂 환경 데이터 원본"):
        for s, df in env_data.items():
            st.markdown(f"**{s}**")
            st.dataframe(df)
            buffer = io.BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                f"{s} CSV 다운로드",
                data=buffer,
                file_name=f"{s}_환경데이터.csv",
                mime="text/csv"
            )

# =============================
# Tab 3: 생육 결과
# =============================
with tab3:
    st.subheader("🥇 EC별 평균 생중량")

    growth_df["EC"] = growth_df["school"].map(EC_CONDITIONS)
    mean_weight = growth_df.groupby("EC")["생중량(g)"].mean().reset_index()

    best_ec = mean_weight.loc[mean_weight["생중량(g)"].idxmax(), "EC"]

    fig_w = px.bar(
        mean_weight,
        x="EC",
        y="생중량(g)",
        title="EC별 평균 생중량"
    )
    fig_w.add_vline(
        x=best_ec,
        line_dash="dash",
        annotation_text="최적 EC ⭐"
    )
    fig_w.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig_w, use_container_width=True)

    metrics = {
        "평균 잎 수": "잎 수(장)",
        "평균 지상부 길이": "지상부 길이(mm)",
        "개체수": "개체번호"
    }

    fig = make_subplots(rows=2, cols=2, subplot_titles=list(metrics.keys()))
    rowcol = [(1,1),(1,2),(2,1)]
    for (title, col), (r,c) in zip(metrics.items(), rowcol):
        tmp = growth_df.groupby("EC")[col].mean().reset_index()
        fig.add_bar(x=tmp["EC"], y=tmp[col], row=r, col=c)

    fig.update_layout(height=600, font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📦 학교별 생중량 분포")
    fig_box = px.box(
        growth_df,
        x="school",
        y="생중량(g)"
    )
    fig_box.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("🔗 상관관계 분석")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            px.scatter(growth_df, x="잎 수(장)", y="생중량(g)"),
            use_container_width=True
        )
    with col2:
        st.plotly_chart(
            px.scatter(growth_df, x="지상부 길이(mm)", y="생중량(g)"),
            use_container_width=True
        )

    with st.expander("📂 생육 데이터 원본"):
        st.dataframe(growth_df)
        buffer = io.BytesIO()
        growth_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        st.download_button(
            "전체 생육 데이터 XLSX 다운로드",
            data=buffer,
            file_name="생육결과_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
