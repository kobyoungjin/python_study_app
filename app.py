# ------------------------------------------------------------
# Streamlit 기반 실시간 미세먼지 대시보드
# 공공데이터포털(에어코리아) API 활용
# ------------------------------------------------------------

import streamlit as st  # 웹 대시보드 프레임워크
import requests  # API 요청 라이브러리
import pandas as pd  # 데이터 처리
import matplotlib.pyplot as plt
import platform
import seaborn as sns  # 고급 시각화

# koreanize_matplotlib 대신 사용하는 한글 설정 코드
from matplotlib import font_manager, rc

if platform.system() == "Windows":
    # 윈도우라면 '맑은 고딕' 폰트 사용
    font_name = font_manager.FontProperties(
        fname="c:/Windows/Fonts/malgun.ttf"
    ).get_name()
    rc("font", family=font_name)
elif platform.system() == "Darwin":
    # 맥(Mac)이라면 'AppleGothic' 사용
    rc("font", family="AppleGothic")

# 마이너스 기호 깨짐 방지
plt.rcParams["axes.unicode_minus"] = False

# ------------------------------------------------------------
# [1] 페이지 기본 설정
# ------------------------------------------------------------

# 웹 페이지 제목, 아이콘 설정
st.set_page_config(page_title="미세먼지 대시보드", page_icon="😷")

# 메인 타이틀
st.title("🌫️ 실시간 대기오염 정보 대시보드")

# 간단한 설명 문구
st.markdown("공공데이터포털 API를 활용하여 **실시간 미세먼지 농도**를 시각화합니다.")

# ------------------------------------------------------------
# [2] 사이드바: 사용자 입력 영역
# ------------------------------------------------------------

st.sidebar.header("옵션 설정")

# API Key 입력
# → type="password" : 화면에 키가 노출되지 않도록 처리
api_key = st.sidebar.text_input("API Key를 입력하세요", type="password")

# 조회 가능한 시·도 목록
sido_list = [
    "서울",
    "부산",
    "대구",
    "인천",
    "광주",
    "대전",
    "울산",
    "경기",
    "강원",
    "충북",
    "충남",
    "전북",
    "전남",
    "경북",
    "경남",
    "제주",
    "세종",
]

# 드롭다운으로 지역 선택
sido_name = st.sidebar.selectbox("조회할 지역을 선택하세요", sido_list)

# ------------------------------------------------------------
# [3] 데이터 로딩 함수 (캐싱 적용)
# ------------------------------------------------------------


# @st.cache_data
# → 같은 API 요청은 다시 호출하지 않고 캐시된 데이터 사용
# → 속도 개선 + 트래픽 절약
@st.cache_data
def load_data(key, region):

    # 시도별 실시간 대기오염 정보 API
    url = (
        "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    )

    # 요청 파라미터
    params = {
        "serviceKey": key,  # 공공데이터포털 인증키
        "returnType": "json",  # JSON 형식
        "numOfRows": "100",  # 한 번에 가져올 데이터 수
        "pageNo": "1",
        "sidoName": region,  # 선택한 시·도
        "ver": "1.0",
    }

    try:
        # API 호출
        response = requests.get(url, params=params, timeout=10)

        # JSON 데이터 파싱
        data = response.json()

        # 실제 측정 데이터 목록
        items = data["response"]["body"]["items"]

        # DataFrame으로 변환
        df = pd.DataFrame(items)

        # ----------------------------------------
        # 필요한 컬럼만 선택 + 한글 컬럼명 변경
        # ----------------------------------------
        select_cols = {
            "stationName": "측정소명",
            "pm10Value": "미세먼지",
            "pm25Value": "초미세먼지",
            "o3Value": "오존",
            "khaiGrade": "통합대기등급",
        }

        df = df[select_cols.keys()].rename(columns=select_cols)

        # ----------------------------------------
        # 문자열 → 숫자형 변환
        # (측정값이 '-' 등으로 오는 경우 대비)
        # ----------------------------------------
        for col in ["미세먼지", "초미세먼지", "오존"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # 결측치 제거 후 반환
        return df.dropna()

    except Exception as e:
        # 에러 발생 시 None 반환
        return None


# ------------------------------------------------------------
# [4] 메인 로직: 버튼 클릭 시 실행
# ------------------------------------------------------------

if st.sidebar.button("데이터 조회하기"):

    # API Key 미입력 시 경고
    if not api_key:
        st.error("API Key를 먼저 입력해주세요!")

    else:
        # 로딩 중 표시
        with st.spinner("데이터를 불러오는 중입니다..."):
            df = load_data(api_key, sido_name)

        # 데이터 로딩 실패 시
        if df is None or df.empty:
            st.error("데이터를 가져오는데 실패했습니다. 키를 확인해주세요.")

        else:
            # ----------------------------------------
            # [4-1] KPI 지표 (평균 / 최고 미세먼지)
            # ----------------------------------------
            avg_pm10 = df["미세먼지"].mean()
            max_pm10 = df["미세먼지"].max()

            col1, col2 = st.columns(2)

            col1.metric(
                label=f"{sido_name} 평균 미세먼지", value=f"{avg_pm10:.1f} ㎍/㎥"
            )

            col2.metric(
                label="최고 농도",
                value=f"{max_pm10:.1f} ㎍/㎥",
                delta="주의 필요" if max_pm10 > 80 else "양호",
            )

            # ----------------------------------------
            # [4-2] 탭 구성
            # ----------------------------------------
            tab1, tab2 = st.tabs(["📊 차트 보기", "📋 데이터 원본"])

            # ---------- 차트 탭 ----------
            with tab1:
                st.subheader(f"{sido_name} 미세먼지 상위 10곳")

                top10 = df.sort_values(by="미세먼지", ascending=False).head(10)

                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(
                    x="측정소명", y="미세먼지", data=top10, palette="Reds_r", ax=ax
                )

                plt.xticks(rotation=45)
                st.pyplot(fig)

            # ---------- 데이터 탭 ----------
            with tab2:
                st.dataframe(df)
