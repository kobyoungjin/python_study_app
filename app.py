import streamlit as st
import requests
from datetime import datetime


# ============================================
# 1️⃣ 날씨 데이터 가져오기 함수
# ============================================
def get_weather_data(lat, lon, api_key):
    # 유저가 제공한 One Call 3.0 URL 양식
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely&appid={api_key}&units=metric&lang=kr"
    response = requests.get(url)
    return response.json()


def get_coords(city_name, api_key):
    # 도시 이름으로 위도/경도를 찾는 Geocoding API
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={api_key}"
    res = requests.get(geo_url).json()
    if res:
        return (
            res[0]["lat"],
            res[0]["lon"],
            res[0]["local_names"].get("ko", res[0]["name"]),
        )
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

            if lat:
                data = get_weather_data(lat, lon, api_key)

                if "current" in data:
                    current = data["current"]

                    # 1. 현재 날씨 대시보드
                    st.subheader(f"🏠 {kor_name}의 현재 날씨")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("온도", f"{current['temp']}°C")
                    col2.metric("습도", f"{current['humidity']}%")
                    col3.metric("날씨", current["weather"][0]["description"])

                    # 날씨 아이콘 표시
                    icon_code = current["weather"][0]["icon"]
                    st.image(f"http://openweathermap.org/img/wn/{icon_code}@2x.png")

                    # 2. 시간별 예보 (간단히 5시간만)
                    st.divider()
                    st.subheader("⏰ 시간별 예보 (향후 5시간)")
                    hourly_cols = st.columns(5)
                    for i in range(5):
                        h_data = data["hourly"][i]
                        time = datetime.fromtimestamp(h_data["dt"]).strftime("%H시")
                        hourly_cols[i].write(f"**{time}**")
                        hourly_cols[i].write(f"{h_data['temp']}°")
                        h_icon = h_data["weather"][0]["icon"]
                        hourly_cols[i].image(
                            f"http://openweathermap.org/img/wn/{h_icon}.png"
                        )

                    # 3. 상세 정보 (JSON 데이터 확인용 - 개발자용)
                    with st.expander("데이터 원문 보기"):
                        st.json(data)
                else:
                    st.error(
                        "날씨 데이터를 가져오지 못했습니다. API 플랜을 확인하세요."
                    )
            else:
                st.error("해당 도시를 찾을 수 없습니다.")
