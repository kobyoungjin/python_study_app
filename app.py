import streamlit as st
import requests
from datetime import datetime


# ============================================
# 1️⃣ 날씨 데이터 가져오기 함수
# ============================================
def get_weather_data(lat, lon, api_key):
    # 3.0(구독형) 대신 2.5(완전 무료형) URL을 사용합니다.
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=kr"
    response = requests.get(url)
    return response.json()


def get_coords(city_name, api_key):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={api_key}"

    try:
        response = requests.get(geo_url)
        res = response.json()

        # [디버깅] 서버에서 받은 응답을 화면에 잠시 보여줍니다.
        # st.write("지오코딩 응답:", res)

        if res and len(res) > 0:
            lat = res[0].get("lat")
            lon = res[0].get("lon")
            local_names = res[0].get("local_names", {})
            kor_name = local_names.get("ko", res[0].get("name"))
            return lat, lon, kor_name

        return None, None, None

    except Exception as e:
        # 에러 메시지를 더 자세히 출력하도록 변경
        st.error(f"좌표 가져오기 실패: {type(e).__name__} - {e}")
        return None, None, None


# ============================================
# 2️⃣ Streamlit UI 구성
# ============================================
st.set_page_config(page_title="매일 날씨", page_icon="🌤️")

# 사이드바: API 키 입력
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("OpenWeather API Key", type="password")
    st.info("One Call API 3.0 키를 입력하세요.")

st.title("🌤️ 실시간 기상 스테이션")

# 도시 입력
city = st.text_input("📍 궁금한 도시 이름을 입력하세요 (영문)", value="Seoul")

if st.button("날씨 확인하기"):
    if not api_key:
        st.error("사이드바에 API Key를 먼저 입력해주세요!")
    else:
        with st.spinner("날씨 정보를 불러오는 중..."):
            lat, lon, kor_name = get_coords(city, api_key)

            if lat is not None:
                data = get_weather_data(lat, lon, api_key)

                # 2.5 버전은 "current" 대신 바로 데이터가 들어있습니다.
                if "main" in data:
                    st.subheader(f"🏠 {kor_name}의 현재 날씨")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("온도", f"{data['main']['temp']}°C")
                    col2.metric("습도", f"{data['main']['humidity']}%")
                    col3.metric("날씨", data["weather"][0]["description"])

                    icon_code = data["weather"][0]["icon"]
                    st.image(f"http://openweathermap.org/img/wn/{icon_code}@2x.png")
                else:
                    st.error("데이터 구조가 다릅니다. API 응답을 확인하세요.")
                    st.write(data)  # 서버가 보낸 메시지 확인 (예: 401, 429 에러 등)
            else:
                st.error("해당 도시를 찾을 수 없습니다.")
