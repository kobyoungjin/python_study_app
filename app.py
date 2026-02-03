import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ============================================
# 🔑 네이버 API 인증 정보
# ============================================
CLIENT_ID = "3wFmO4IX2aqtsq0vRoX4".strip()
CLIENT_SECRET = "rtI9nZHrOw".strip()


def clean_title(title):
    return (
        title.replace("<b>", "")
        .replace("</b>", "")
        .replace("&quot;", '"')
        .replace("&amp;", "&")
    )


def search_news(keyword, display_count=100):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    params = {"query": keyword, "display": display_count, "sort": "date"}
    return requests.get(url, headers=headers, params=params)


# ------------------------------------------------
# Streamlit UI
# ------------------------------------------------
st.set_page_config(page_title="뉴스 엑셀 저장기", layout="wide")
st.title("📥 뉴스 검색 및 엑셀 저장")

# 사이드바 설정
with st.sidebar:
    selected_date = st.date_input("조회 날짜", datetime.now())
    display_limit = st.slider("검색 건수", 10, 100, 50)

keyword = st.text_input("🔍 검색어를 입력하세요")

if st.button("뉴스 검색") and keyword:
    with st.spinner("데이터를 가져오는 중..."):
        response = search_news(keyword, display_limit)

        if response.status_code == 200:
            items = response.json().get("items", [])
            filtered_items = []

            for item in items:
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
                st.success(f"{len(filtered_items)}건의 뉴스를 찾았습니다.")

                # 1. 데이터프레임 생성 및 화면 표시
                df = pd.DataFrame(filtered_items)
                st.dataframe(df, use_container_width=True)  # 표 형태로 보여줌

                # 2. 엑셀(CSV) 변환 및 다운로드 버튼
                # 한글 깨짐 방지를 위해 utf-8-sig 사용
                csv_data = df.to_csv(index=False, encoding="utf-8-sig")

                st.download_button(
                    label="📂 검색 결과 엑셀(CSV) 다운로드",
                    data=csv_data,
                    file_name=f"news_{keyword}_{selected_date}.csv",
                    mime="text/csv",
                )

            else:
                st.warning("선택한 날짜에 해당하는 뉴스가 검색 범위 내에 없습니다.")
        else:
            st.error("API 요청에 실패했습니다. 키 값을 확인하세요.")
