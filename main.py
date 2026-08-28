```python
import streamlit as st
import pandas as pd

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="서울 역대 기온 순위",
    page_icon="🌡️",
    layout="centered"
)

# --------------------------------------------------
# 스타일
# --------------------------------------------------
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }

    .title {
        font-size: 2.3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.3rem;
    }

    .subtitle {
        text-align: center;
        color: #64748b;
        margin-bottom: 2rem;
    }

    .result-card {
        background: white;
        padding: 28px;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.07);
        text-align: center;
        margin-top: 25px;
    }

    .rank {
        font-size: 3.5rem;
        font-weight: 900;
        color: #2563eb;
        line-height: 1.1;
    }

    .rank-total {
        font-size: 1rem;
        color: #64748b;
    }

    .temperature {
        font-size: 2rem;
        font-weight: 800;
        margin-top: 12px;
    }

    .period {
        color: #475569;
        margin-top: 8px;
    }

    .info-box {
        background: #eff6ff;
        border-radius: 14px;
        padding: 16px;
        margin-top: 15px;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
@st.cache_data
def load_data():
    # 요청한 파일 경로
    file_path = "seoul csv"

    df = pd.read_csv(file_path)

    # 날짜 앞뒤 공백 제거
    df["날짜"] = df["날짜"].astype(str).str.strip()

    # 날짜 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 평균기온 숫자 변환
    df["평균기온"] = pd.to_numeric(
        df["평균기온"],
        errors="coerce"
    )

    # 날짜와 평균기온이 모두 있는 데이터만 사용
    df = df.dropna(subset=["날짜", "평균기온"])

    # 날짜순 정렬
    df = df.sort_values("날짜").reset_index(drop=True)

    return df


df = load_data()


# --------------------------------------------------
# 제목
# --------------------------------------------------
st.markdown(
    '<div class="title">🌡️ 서울 역대 기온 순위</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    '원하는 기간을 선택하면 같은 기간 길이의 역대 기온과 비교합니다.'
    '</div>',
    unsafe_allow_html=True
)


# --------------------------------------------------
# 데이터 정보
# --------------------------------------------------
min_date = df["날짜"].min().date()
max_date = df["날짜"].max().date()

st.caption(
    f"📊 분석 데이터: {min_date.strftime('%Y-%m-%d')} ~ "
    f"{max_date.strftime('%Y-%m-%d')}"
)


# --------------------------------------------------
# 날짜 선택
# --------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "시작 날짜",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )

with col2:
    end_date = st.date_input(
        "종료 날짜",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )


# --------------------------------------------------
# 날짜 오류 확인
# --------------------------------------------------
if start_date > end_date:
    st.error("⚠️ 시작 날짜가 종료 날짜보다 늦습니다.")
    st.stop()


# --------------------------------------------------
# 선택 기간 분석
# --------------------------------------------------
selected_start = pd.Timestamp(start_date)
selected_end = pd.Timestamp(end_date)

selected = df[
    (df["날짜"] >= selected_start) &
    (df["날짜"] <= selected_end)
].copy()

if selected.empty:
    st.error("선택한 기간에 기온 데이터가 없습니다.")
    st.stop()


# 실제 데이터가 존재하는 날짜 수
actual_days = len(selected)

# 달력상 기간
period_days = (selected_end - selected_start).days + 1

# 선택 기간 평균기온
selected_mean = selected["평균기온"].mean()


# --------------------------------------------------
# 역대 기간별 비교
#
# 선택한 기간과 동일한 '날짜 수'를 갖는
# 모든 연속 기간을 비교합니다.
# --------------------------------------------------
daily = (
    df[["날짜", "평균기온"]]
    .dropna()
    .sort_values("날짜")
    .drop_duplicates("날짜")
    .reset_index(drop=True)
)

# 날짜를 인덱스로 설정
daily_indexed = daily.set_index("날짜")

# 선택 기간의 실제 데이터 날짜 수를 기준으로 비교
window_size = actual_days

historical_results = []

values = daily_indexed["평균기온"].values
dates = daily_indexed.index

# 연속된 데이터 구간을 찾기 위해 날짜 차이를 확인
for i in range(len(daily) - window_size + 1):

    window = daily.iloc[i:i + window_size]

    # 실제 날짜가 연속되지 않는 경우 제외
    date_diff = (
        window["날짜"].iloc[-1] -
        window["날짜"].iloc[0]
    ).days + 1

    if date_diff != window_size:
        continue

    window_mean = window["평균기온"].mean()

    historical_results.append({
        "start": window["날짜"].iloc[0],
        "end": window["날짜"].iloc[-1],
        "mean": window_mean
    })


historical = pd.DataFrame(historical_results)


# --------------------------------------------------
# 선택 기간과 동일한 구간 제거
# --------------------------------------------------
if not historical.empty:

    historical = historical[
        ~(
            (historical["start"] == selected_start) &
            (historical["end"] == selected_end)
        )
    ].copy()


# --------------------------------------------------
# 순위 계산
#
# 기온이 높을수록 1위
# --------------------------------------------------
if historical.empty:

    rank = 1
    total_periods = 1

else:

    # 선택 기간을 포함한 전체 결과
    all_results = pd.concat([
        historical,
        pd.DataFrame([{
            "start": selected_start,
            "end": selected_end,
            "mean": selected_mean
        }])
    ], ignore_index=True)

    # 평균기온 높은 순으로 정렬
    all_results = all_results.sort_values(
        "mean",
        ascending=False
    ).reset_index(drop=True)

    # 동점은 같은 순위
    all_results["rank"] = (
        all_results["mean"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    selected_row = all_results[
        (all_results["start"] == selected_start) &
        (all_results["end"] == selected_end)
    ].iloc[0]

    rank = int(selected_row["rank"])
    total_periods = len(all_results)


# --------------------------------------------------
# 결과 카드
# --------------------------------------------------
st.markdown(
    f"""
    <div class="result-card">

        <div style="font-size:1rem; color:#64748b;">
            선택 기간 평균기온
        </div>

        <div class="temperature">
            {selected_mean:.1f}℃
        </div>

        <div class="period">
            {start_date.strftime('%Y년 %m월 %d일')}
            ~
            {end_date.strftime('%Y년 %m월 %d일')}
        </div>

        <hr style="border:none; border-top:1px solid #e2e8f0; margin:22px 0;">

        <div style="font-size:1rem; color:#64748b;">
            역대 기온 순위
        </div>

        <div class="rank">
            {rank:,}위
        </div>

        <div class="rank-total">
            비교 가능한 전체 기간 {total_periods:,}개 중
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# 보조 정보
# --------------------------------------------------
st.write("")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "평균기온",
        f"{selected_mean:.1f} ℃"
    )

with c2:
    st.metric(
        "최고기온",
        f"{selected['최고기온'].max():.1f} ℃"
        if "최고기온" in selected.columns
        else "-"
    )

with c3:
    st.metric(
        "최저기온",
        f"{selected['최저기온'].min():.1f} ℃"
        if "최저기온" in selected.columns
        else "-"
    )


# --------------------------------------------------
# 데이터 안내
# --------------------------------------------------
st.markdown(
    f"""
    <div class="info-box">
    💡 <b>순위 산정 방법</b><br>
    선택한 기간과 동일한 길이의 연속된 과거 기간을 모두 계산한 뒤,
    <b>평균기온이 높은 순서</b>로 순위를 산정합니다.<br><br>
    선택 기간: <b>{period_days}일</b>
    </div>
    """,
    unsafe_allow_html=True
)
```
