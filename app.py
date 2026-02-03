import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# ============================================
# 1️⃣ 데이터 처리 함수
# ============================================


def get_coords(city_name, api_key):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={api_key}"
    try:
        res = requests.get(geo_url).json()
        if res:
            lat, lon = res[0]["lat"], res[0]["lon"]
            kor_name = res[0].get("local_names", {}).get("ko", res[0]["name"])
            return lat, lon, kor_name
        return None, None, None
    except:
        return None, None, None


def get_weather_data(lat, lon, api_key):
    # 무료 버전(2.5) API 사용
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=kr"
    return requests.get(url).json()


def get_outfit_suggestion(temp):
    """온도에 따른 옷차림 추천 로직"""
    if temp >= 28:
        return "👕 민소매, 반바지, 린넨 옷이 좋아요. 자외선 차단제는 필수!"
    elif 23 <= temp < 28:
        return "👕 반팔, 얇은 셔츠, 반바지, 면바지를 추천해요."
    elif 20 <= temp < 23:
        return "🚩 긴팔 티, 가디건, 후드티, 면바지, 슬랙스가 적당해요."
    elif 17 <= temp < 20:
        return "🧥 얇은 니트, 맨투맨, 가디건, 청바지를 입으세요."
    elif 12 <= temp < 17:
        return "🧥 자켓, 가디건, 야상, 스타킹, 청바지, 면바지가 좋아요."
    elif 9 <= temp < 12:
        return "🧥 트렌치코트, 야상, 여러 겹 껴입기가 필요해요."
    elif 5 <= temp < 9:
        return "🧥 코트, 가죽 자켓, 히트텍, 니트, 레깅스를 추천합니다."
    else:
        return "🧤 패딩, 두꺼운 코트, 목도리, 기모 제품으로 무장하세요!"


# ============================================
# 2️⃣ Streamlit UI 구성
# ============================================
st.set_page_config(page_title="AI 기상 캐스터", page_icon="🌈", layout="wide")

with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("OpenWeather API Key", type="password")
    st.info("API 키를 입력하고 도시를 검색하세요.")

st.title("🌈 AI 기상 캐스터 & 스타일 가이드")

city = st.text_input("📍 궁금한 도시 이름을 입력하세요 (영문)", value="Seoul")

if st.button("날씨 및 스타일 확인"):
    if not api_key:
        st.error("사이드바에 API Key를 먼저 입력해주세요!")
    else:
        lat, lon, kor_name = get_coords(city, api_key)

        if lat:
            data = get_weather_data(lat, lon, api_key)

            if "main" in data:
                # 1. 날씨 정보 섹션
                temp = data["main"]["temp"]
                weather_desc = data["weather"][0]["description"]

                st.subheader(f"🏠 {kor_name}의 현재 기상 상황")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("온도", f"{temp}°C")
                c2.metric("체감", f"{data['main']['feels_like']}°C")
                c3.metric("습도", f"{data['main']['humidity']}%")
                c4.metric("날씨", weather_desc)

                # 2. 옷차림 추천 섹션 (중요 포인트!)
                st.divider()
                st.subheader("👗 오늘의 추천 옷차림")
                suggestion = get_outfit_suggestion(temp)
                st.info(f"**현재 기온({temp}°C) 기준:** \n\n {suggestion}")

                # 3. 지도 및 상세 정보 섹션
                st.divider()
                left_col, right_col = st.columns([1, 1])

                with left_col:
                    st.subheader("📍 위치 확인")
                    # 위도, 경도 데이터를 데이터프레임으로 변환
                    map_data = pd.DataFrame({"lat": [lat], "lon": [lon]})
                    # Streamlit 내장 지도로 표시 (매우 가볍고 빠름)
                    st.map(map_data)

                with right_col:
                    st.subheader("📊 추가 정보")
                    st.write(
                        f"- 일출: {datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')}"
                    )
                    st.write(
                        f"- 일몰: {datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')}"
                    )
                    st.write(f"- 풍속: {data['wind']['speed']} m/s")
                    icon_code = data["weather"][0]["icon"]
                    st.image(
                        f"http://openweathermap.org/img/wn/{icon_code}@2x.png",
                        width=100,
                    )
            else:
                st.error("데이터를 가져오는 데 실패했습니다.")
        else:
            st.warning(f"'{city}' 도시를 찾을 수 없습니다.")
