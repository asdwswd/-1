```python
import streamlit as st
import pandas as pd
from pathlib import Path

# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="서울 역대 기온 순위",
    page_icon="🌡️",
    layout="centered"
)

# =========================================================
# 데이터 파일 경로
# =========================================================
FILE_PATH = "seoul csv"


# =========================================================
# 데이터 불러오기
# =========================================================
@st.cache_data
def load_data():

    # 요청한 파일 경로
    path = Path(FILE_PATH)

    # 파일이 없을 경우 오류 메시지
    if not path.exists():
        st.error(
            f"데이터 파일을 찾을 수 없습니다.\n\n"
            f"GitHub Repository의 파일명을 정확히 "
            f"'{FILE_PATH}'로 올려주세요."
        )
        st.stop()

    # CSV 읽기
    data = pd.read_csv(path)

    # 컬럼명 공백 제거
    data.columns = data.columns.str.strip()

    # 날짜 앞뒤 공백 및 탭 제거
    data["날짜"] = (
        data["날짜"]
        .astype(str)
        .str.strip()
        .str.replace("\t", "", regex=False)
    )

    # 날짜 변환
    data["날짜"] = pd.to_datetime(
        data["날짜"],
        errors="coerce"
    )

    # 기온 숫자로 변환
    for column in ["평균기온", "최저기온", "최고기온"]:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

    # 날짜와 평균기온이 없는 행 제거
    data = data.dropna(
        subset=["날짜", "평균기온"]
    )

    # 날짜순 정렬
    data = data.sort_values("날짜")

    # 같은 날짜가 여러 개라면 첫 번째만 사용
    data = data.drop_duplicates(
        subset=["날짜"],
        keep="first"
    )

    data = data.reset_index(drop=True)

    return data


df = load_data()


# =========================================================
# 제목
# =========================================================
st.markdown(
    """
    <div style="
        text-align:center;
        padding:20px 0 10px 0;
    ">
        <h1 style="font-size:36px; margin-bottom:5px;">
            🌡️ 서울 역대 기온 순위
        </h1>

        <p style="
            color:#6b7280;
            font-size:16px;
        ">
            두 날짜를 선택하면 해당 기간의 평균기온이
            역대 몇 위인지 확인할 수 있습니다.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 데이터 기간
# =========================================================
min_date = df["날짜"].min().date()
max_date = df["날짜"].max().date()


st.caption(
    f"📊 데이터 기간: "
    f"{min_date.strftime('%Y-%m-%d')} ~ "
    f"{max_date.strftime('%Y-%m-%d')}"
)


# =========================================================
# 날짜 선택
# =========================================================
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "📅 시작 날짜",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )

with col2:
    end_date = st.date_input(
        "📅 종료 날짜",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )


# =========================================================
# 날짜 오류 체크
# =========================================================
if start_date > end_date:

    st.warning(
        "⚠️ 시작 날짜가 종료 날짜보다 늦습니다. "
        "날짜를 다시 선택해주세요."
    )

    st.stop()


# =========================================================
# 선택한 기간
# =========================================================
start = pd.Timestamp(start_date)
end = pd.Timestamp(end_date)

selected = df[
    (df["날짜"] >= start) &
    (df["날짜"] <= end)
].copy()


if len(selected) == 0:

    st.error(
        "선택한 기간에 기온 데이터가 없습니다."
    )

    st.stop()


# =========================================================
# 선택 기간의 길이
# =========================================================
period_days = (
    end - start
).days + 1


# =========================================================
# 선택 기간 평균기온
# =========================================================
selected_mean = selected["평균기온"].mean()


# =========================================================
# 역대 동일 기간 길이 비교
#
# 예:
# 7월 1일 ~ 7월 7일 선택
# → 7일짜리 모든 과거 기간과 비교
# =========================================================

historical = []

for i in range(len(df) - period_days + 1):

    window = df.iloc[
        i:i + period_days
    ]

    # 날짜가 실제로 연속되어 있는지 확인
    first_day = window["날짜"].iloc[0]
    last_day = window["날짜"].iloc[-1]

    actual_length = (
        last_day - first_day
    ).days + 1

    if actual_length != period_days:
        continue

    average_temperature = (
        window["평균기온"].mean()
    )

    historical.append({
        "시작일": first_day,
        "종료일": last_day,
        "평균기온": average_temperature
    })


historical_df = pd.DataFrame(historical)


# =========================================================
# 선택 기간을 비교 목록에 추가
# =========================================================
selected_row = pd.DataFrame([{
    "시작일": start,
    "종료일": end,
    "평균기온": selected_mean
}])


comparison = pd.concat(
    [historical_df, selected_row],
    ignore_index=True
)


# =========================================================
# 평균기온 높은 순으로 정렬
# =========================================================
comparison = comparison.sort_values(
    "평균기온",
    ascending=False
).reset_index(drop=True)


# =========================================================
# 순위 계산
# =========================================================
comparison["순위"] = (
    comparison["평균기온"]
    .rank(
        method="min",
        ascending=False
    )
    .astype(int)
)


# 선택한 기간의 순위 찾기
selected_rank = comparison.loc[
    (
        (comparison["시작일"] == start) &
        (comparison["종료일"] == end)
    ),
    "순위"
].iloc[0]


selected_rank = int(selected_rank)

total_count = len(comparison)


# =========================================================
# 결과 화면
# =========================================================

st.markdown(
    f"""
    <div style="
        background:linear-gradient(
            135deg,
            #eff6ff,
            #ffffff
        );
        border-radius:24px;
        padding:35px 20px;
        text-align:center;
        margin-top:25px;
        margin-bottom:25px;
        border:1px solid #dbeafe;
    ">

        <div style="
            color:#64748b;
            font-size:15px;
            margin-bottom:8px;
        ">
            선택한 기간
        </div>

        <div style="
            font-size:20px;
            font-weight:700;
            color:#1e293b;
        ">
            {start_date.strftime('%Y년 %m월 %d일')}
            ~
            {end_date.strftime('%Y년 %m월 %d일')}
        </div>

        <div style="
            margin-top:28px;
            color:#64748b;
            font-size:15px;
        ">
            평균기온
        </div>

        <div style="
            font-size:38px;
            font-weight:800;
            color:#0f172a;
            margin:5px 0 25px 0;
        ">
            {selected_mean:.1f}℃
        </div>

        <div style="
            color:#64748b;
            font-size:15px;
        ">
            역대 기온 순위
        </div>

        <div style="
            font-size:64px;
            line-height:1.1;
            font-weight:900;
            color:#2563eb;
            margin:5px 0;
        ">
            {selected_rank:,}위
        </div>

        <div style="
            color:#64748b;
            font-size:14px;
        ">
            동일한 {period_days}일 기간
            {total_count:,}개 중
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 상세 지표
# =========================================================
st.subheader("📌 선택 기간 상세 정보")

metric1, metric2, metric3 = st.columns(3)


with metric1:

    st.metric(
        "평균기온",
        f"{selected_mean:.1f}℃"
    )


with metric2:

    if "최고기온" in selected.columns:

        highest = selected["최고기온"].max()

        st.metric(
            "최고기온",
            f"{highest:.1f}℃"
        )

    else:

        st.metric(
            "최고기온",
            "-"
        )


with metric3:

    if "최저기온" in selected.columns:

        lowest = selected["최저기온"].min()

        st.metric(
            "최저기온",
            f"{lowest:.1f}℃"
        )

    else:

        st.metric(
            "최저기온",
            "-"
        )


# =========================================================
# 해석
# =========================================================

if selected_rank == 1:

    message = (
        "🔥 역대 가장 따뜻한 기간입니다!"
    )

elif selected_rank <= 10:

    message = (
        f"🔥 역대 상위 {selected_rank}위에 해당하는 "
        "매우 따뜻한 기간입니다."
    )

else:

    message = (
        f"📊 역대 {total_count:,}개 기간 중 "
        f"{selected_rank:,}위입니다."
    )


st.info(message)


# =========================================================
# 순위표
# =========================================================
with st.expander("🔎 전체 비교 결과 보기"):

    display_df = comparison.copy()

    display_df["시작일"] = (
        display_df["시작일"]
        .dt.strftime("%Y-%m-%d")
    )

    display_df["종료일"] = (
        display_df["종료일"]
        .dt.strftime("%Y-%m-%d")
    )

    display_df["평균기온"] = (
        display_df["평균기온"]
        .round(1)
    )

    display_df = display_df[
        [
            "순위",
            "시작일",
            "종료일",
            "평균기온"
        ]
    ]

    display_df.columns = [
        "순위",
        "시작일",
        "종료일",
        "평균기온(℃)"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 하단 안내
# =========================================================
st.markdown(
    """
    <div style="
        text-align:center;
        color:#94a3b8;
        font-size:13px;
        padding:30px 0 10px 0;
    ">
        서울 기상관측 데이터를 기반으로 계산한 결과입니다.
    </div>
    """,
    unsafe_allow_html=True
)
```
