import streamlit as st
import requests
import pandas as pd


# ============================================
# 1️⃣ 공공데이터 API 호출 함수
# ============================================
def get_food_data(api_key, city_code, page_num=1):
    # 지방행정인허가 데이터 개방 API URL (예시: 휴게음식점)
    url = "https://apis.data.go.kr/1741000/rest_cafes//info"

    params = {
        "authKey": api_key.strip(),
        "lastModTs": "",  # 최종수정일자 (선택)
        "opnSvcId": "07_24_05_P",  # 휴게음식점 서비스 코드
        "pageIndex": page_num,
        "pageSize": 20,
        "resultType": "json",
    }

    try:
        response = requests.get(url, params=params)
        return response
    except Exception as e:
        return None


# ============================================
# 2️⃣ Streamlit UI 구성
# ============================================
st.set_page_config(page_title="전국 휴게음식점 조회", layout="wide")

# 사이드바 구성
with st.sidebar:
    st.header("🔑 API 인증 설정")
    # 공공데이터포털에서 발급받은 Decoding 인증키 입력
    auth_key = st.text_input(
        "공공데이터 인증키(Decoding)",
        type="password",
        placeholder="인증키를 입력하세요",
    )

    st.divider()

    st.header("🔍 검색 필터")
    # 실제로는 구/군 코드를 선택하게 할 수 있습니다.
    city_name = st.text_input("지역명 입력", value="천안시")
    search_limit = st.number_input("조회 페이지 수", min_value=1, max_value=10, value=1)

    st.info("💡 공공데이터포털의 '지방행정인허가' API를 사용합니다.")

st.title("🍔 휴게음식점 인허가 정보 조회")
st.write(f"현재 **{city_name}** 지역의 휴게음식점 정보를 불러옵니다.")

# 조회 버튼
if st.button("데이터 불러오기"):
    if not auth_key:
        st.error("사이드바에 API 인증키를 먼저 입력해 주세요!")
    else:
        with st.spinner("데이터 수집 중..."):
            response = get_food_data(auth_key, city_name, search_limit)

            if response and response.status_code == 200:
                try:
                    data = response.json()
                    # API 응답 구조에 따라 경로 수정 필요 (보통 resultCode나 row에 데이터 위치)
                    items = data.get("result", {}).get("row", [])

                    if items:
                        df = pd.DataFrame(items)

                        # 주요 컬럼만 선별해서 보여주기
                        columns_to_show = [
                            "BPLCNM",
                            "RDNWHALADDRESS",
                            "TRDSTATENM",
                            "UPTAYNM",
                        ]
                        # 컬럼 이름 한글로 변경
                        df_display = df[columns_to_show].rename(
                            columns={
                                "BPLCNM": "사업장명",
                                "RDNWHALADDRESS": "도로명주소",
                                "TRDSTATENM": "영업상태",
                                "UPTAYNM": "업태명",
                            }
                        )

                        st.success(f"총 {len(df_display)}개의 업소를 찾았습니다.")
                        st.dataframe(df_display, use_container_width=True)

                        # CSV 다운로드 기능
                        csv = df_display.to_csv(index=False, encoding="utf-8-sig")
                        st.download_button(
                            "📥 결과 다운로드(CSV)",
                            data=csv,
                            file_name=f"{city_name}_휴게음식점.csv",
                        )
                    else:
                        st.warning(
                            "조회된 데이터가 없습니다. 지역명이나 페이지를 확인하세요."
                        )
                except:
                    st.error(
                        "데이터 해석 중 오류가 발생했습니다. API 키가 정확한지 확인하세요."
                    )
            else:
                st.error("API 서버 응답 실패. 인증키 또는 네트워크 상태를 확인하세요.")
