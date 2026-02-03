import streamlit as st
import requests
import pandas as pd
from datetime import datetime


# ------------------------------------------------
# 1️⃣ 데이터 처리 함수들
# ------------------------------------------------
def clean_title(title):
    return (
        title.replace("<b>", "")
        .replace("</b>", "")
        .replace("&quot;", '"')
        .replace("&amp;", "&")
    )


def search_news(keyword, client_id, client_secret, display_count=100):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id.strip(),
        "X-Naver-Client-Secret": client_secret.strip(),
    }
    params = {"query": keyword, "display": display_count, "sort": "date"}
    return requests.get(url, headers=headers, params=params)


# ------------------------------------------------
# 2️⃣ Streamlit UI 구성
# ------------------------------------------------
st.set_page_config(page_title="뉴스 엑셀 저장기", layout="wide")

# 사이드바에서 API 키 입력 받기
with st.sidebar:
    st.header("🔑 API 인증 설정")
    # type="password"를 넣으면 입력값이 별표(***)로 가려집니다.
    input_id = st.text_input("Naver Client ID", placeholder="아이디를 입력하세요")
    input_secret = st.text_input(
        "Naver Client Secret", placeholder="시크릿을 입력하세요", type="password"
    )

    st.divider()  # 구분선

    st.header("📅 검색 설정")
    selected_date = st.date_input("조회 날짜", datetime.now())
    display_limit = st.slider("검색 건수 (최신순 범위)", 10, 100, 50)

st.title("📰 실시간 뉴스 검색 및 저장")

# 메인 검색창
keyword = st.text_input("🔍 검색어를 입력하세요", placeholder="예: 삼성전자, AI, 금리")

if st.button("뉴스 검색하기"):
    # 키 입력 여부 확인
    if not input_id or not input_secret:
        st.error("왼쪽 사이드바에 Naver API 키를 먼저 입력해 주세요!")
    elif not keyword:
        st.warning("검색어를 입력해 주세요.")
    else:
        with st.spinner("뉴스를 가져오는 중..."):
            response = search_news(keyword, input_id, input_secret, display_limit)

            if response.status_code == 200:
                items = response.json().get("items", [])
                filtered_items = []

                for item in items:
                    # 날짜 비교 로직
                    pub_date = datetime.strptime(
                        item["pubDate"], "%a, %d %b %Y %H:%M:%S +0900"
                    ).date()
                    if pub_date == selected_date:
                        filtered_items.append(
                            {
                                "날짜": item["pubDate"],
                                "제목": clean_title(item["title"]),
                                "링크": item["link"],
                                "요약": clean_title(item["description"]),
                            }
                        )

                if filtered_items:
                    st.success(
                        f"'{selected_date}' 날짜 뉴스 {len(filtered_items)}건을 찾았습니다."
                    )
                    df = pd.DataFrame(filtered_items)
                    st.dataframe(df, use_container_width=True)

                    # 엑셀 다운로드 버튼 (한글 깨짐 방지 utf-8-sig)
                    csv_data = df.to_csv(index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="📥 엑셀(CSV) 다운로드",
                        data=csv_data,
                        file_name=f"news_{keyword}_{selected_date}.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning(
                        f"선택한 날짜({selected_date})의 뉴스가 검색 결과 상위 {display_limit}건 내에 없습니다. 검색 건수를 늘려보세요."
                    )

            elif response.status_code == 401:
                st.error("인증 실패! API 키(ID/Secret)를 다시 확인해 주세요.")
            else:
                st.error(f"오류가 발생했습니다 (코드: {response.status_code})")
