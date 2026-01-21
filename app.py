import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# =======================
# DB 설정
# =======================
conn = sqlite3.connect("bmi.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS bmi_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    date TEXT,
    height REAL,
    weight REAL,
    bmi REAL,
    status TEXT
)
"""
)
conn.commit()


# =======================
# 함수
# =======================
def bmi_calc(height, weight):
    return weight / ((height / 100) ** 2)


def bmi_status(bmi):
    if bmi >= 35:
        return "고도 비만"
    elif bmi >= 30:
        return "2단계 비만"
    elif bmi >= 25:
        return "1단계 비만"
    elif bmi >= 23:
        return "과체중"
    elif bmi >= 18.5:
        return "정상"
    else:
        return "저체중"


def load_data():
    return pd.read_sql("SELECT * FROM bmi_history ORDER BY date", conn)


# =======================
# 추가 함수 (칼로리)
# =======================
def calc_bmr(weight, height, age, gender):
    if gender == "남성":
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161


def calc_tdee(bmr, activity):
    activity_map = {
        "거의 없음": 1.2,
        "가벼움 (주1~3회)": 1.375,
        "보통 (주3~5회)": 1.55,
        "높음 (주6~7회)": 1.725,
    }
    return bmr * activity_map[activity]


def calorie_plan(tdee, bmi, target_bmi):
    if bmi > target_bmi + 1:
        return tdee - 500, "감량"
    elif bmi < target_bmi - 1:
        return tdee + 300, "증량"
    else:
        return tdee, "유지"


def workout_recommendation(plan_type):
    if plan_type == "감량":
        return {
            "title": "🔥 체지방 감량 프로그램",
            "content": """
- 유산소: 빠르게 걷기 / 러닝 / 자전거 (30~40분, 주 4~5회)
- 근력: 전신 서킷 (주 2~3회)
- 포인트: 공복 유산소 ❌ / 꾸준함 ⭕
""",
        }
    elif plan_type == "유지":
        return {
            "title": "⚖️ 체형 유지 프로그램",
            "content": """
- 유산소: 가벼운 조깅 또는 수영 (20~30분, 주 2~3회)
- 근력: 상·하체 분할 (주 3회)
- 포인트: 운동 루틴 고정
""",
        }
    else:
        return {
            "title": "💪 근육 증가 프로그램",
            "content": """
- 근력: 중량 훈련 (주 4~5회)
- 유산소: 최소화 (10~15분)
- 포인트: 점진적 과부하 + 충분한 휴식
""",
        }


def create_pdf_report(filename, user_name, latest, bmr, tdee, rec_cal, plan_type):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []

    story.append(Paragraph(f"<b>개인 건강 리포트</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"이름: {user_name}", styles["Normal"]))
    story.append(Paragraph(f"날짜: {latest['date']}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>BMI 요약</b>", styles["Heading2"]))
    story.append(
        Paragraph(f"BMI: {latest['bmi']} ({latest['status']})", styles["Normal"])
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>칼로리 분석</b>", styles["Heading2"]))
    story.append(Paragraph(f"BMR: {int(bmr)} kcal", styles["Normal"]))
    story.append(Paragraph(f"TDEE: {int(tdee)} kcal", styles["Normal"]))
    story.append(
        Paragraph(
            f"권장 섭취 칼로리: {int(rec_cal)} kcal ({plan_type})", styles["Normal"]
        )
    )
    story.append(Spacer(1, 12))

    workout = workout_recommendation(plan_type)
    story.append(Paragraph("<b>운동 추천</b>", styles["Heading2"]))
    story.append(Paragraph(workout["content"].replace("\n", "<br/>"), styles["Normal"]))

    doc.build(story)


# =======================
# 페이지 설정
# =======================
st.set_page_config(page_title="개인 건강 대시보드", layout="wide")
st.title("📊 개인 건강 대시보드 (BMI)")

# =======================
# 사이드바 : 개인정보
# =======================
st.sidebar.header("👤 개인정보")

name = st.sidebar.text_input("이름")
height = st.sidebar.number_input("키 (cm)", min_value=0.0, step=1.0)
weight = st.sidebar.number_input("몸무게 (kg)", min_value=0.0, step=0.1)
target_bmi = st.sidebar.number_input(
    "🎯 목표 BMI", min_value=10.0, max_value=40.0, value=22.0
)

if st.sidebar.button("➕ BMI 기록 저장"):
    if not name:
        st.sidebar.error("이름을 입력하세요.")
    elif height <= 0:
        st.sidebar.error("키는 0보다 커야 합니다.")
    else:
        bmi = bmi_calc(height, weight)
        status = bmi_status(bmi)

        cursor.execute(
            """
        INSERT INTO bmi_history (name, date, height, weight, bmi, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                name,
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                height,
                weight,
                round(bmi, 2),
                status,
            ),
        )
        conn.commit()
        st.sidebar.success(f"저장 완료 (BMI {bmi:.2f})")
        st.rerun()

st.sidebar.subheader("🧍 신체 정보")

gender = st.sidebar.radio("성별", ["남성", "여성"])
age = st.sidebar.number_input("나이", min_value=10, max_value=100, value=30)
activity = st.sidebar.selectbox(
    "활동량", ["거의 없음", "가벼움 (주1~3회)", "보통 (주3~5회)", "높음 (주6~7회)"]
)


# =======================
# 메인 대시보드
# =======================
df = load_data()

if df.empty:
    st.info("왼쪽 사이드바에서 정보를 입력해 BMI를 기록하세요.")
    st.stop()

selected_name = st.selectbox("분석할 사용자 선택", sorted(df["name"].unique()))
user_df = df[df["name"] == selected_name].sort_values("date")

if user_df.empty:
    st.warning("선택한 사용자의 기록이 없습니다.")
    st.stop()

latest = user_df.iloc[-1]
prev = user_df.iloc[-2] if len(user_df) > 1 else None

st.subheader("🔥 칼로리 분석")

bmr = calc_bmr(latest["weight"], latest["height"], age, gender)
tdee = calc_tdee(bmr, activity)
recommended_cal, plan_type = calorie_plan(tdee, latest["bmi"], target_bmi)

c1, c2, c3 = st.columns(3)
c1.metric("기초대사량(BMR)", f"{int(bmr)} kcal")
c2.metric("유지 칼로리(TDEE)", f"{int(tdee)} kcal")
c3.metric("권장 섭취 칼로리", f"{int(recommended_cal)} kcal", plan_type)

st.subheader("🏃 운동 추천")

workout = workout_recommendation(plan_type)
st.markdown(f"### {workout['title']}")
st.info(workout["content"])


# =======================
# PDF 리포트 다운로드
st.subheader("📄 건강 리포트 다운로드")

if st.button("PDF 리포트 생성"):
    pdf_path = f"{selected_name}_health_report.pdf"

    create_pdf_report(
        pdf_path, selected_name, latest, bmr, tdee, recommended_cal, plan_type
    )

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="📥 PDF 다운로드", data=f, file_name=pdf_path, mime="application/pdf"
        )


# =======================
# KPI 카드
# =======================
st.subheader("📌 핵심 지표")

c1, c2, c3, c4 = st.columns(4)

c1.metric("최근 BMI", latest["bmi"])
c2.metric("판정", latest["status"])
c3.metric("최고 BMI", user_df["bmi"].max())
c4.metric("최저 BMI", user_df["bmi"].min())

# =======================
# BMI 변화 분석
# =======================
st.subheader("📈 BMI 변화 추이")
st.line_chart(user_df.set_index("date")["bmi"])

# =======================
# AI 스타일 분석 코멘트
# =======================
st.subheader("🧠 분석 리포트")

diff = latest["bmi"] - target_bmi

if diff > 3:
    st.error("⚠️ 목표 BMI 대비 위험 수준입니다. 체중 관리가 필요합니다.")
elif diff > 1:
    st.warning("📉 목표 BMI보다 다소 높습니다. 식단/운동 관리가 필요합니다.")
elif diff > -1:
    st.success("✅ 목표 BMI 범위 내에 있습니다. 잘 관리되고 있습니다.")
else:
    st.info("📈 목표 BMI보다 낮습니다. 건강 상태를 점검하세요.")

if prev is not None:
    delta = latest["bmi"] - prev["bmi"]
    if delta > 0:
        st.warning(f"최근 기록 대비 BMI가 {delta:.2f} 증가했습니다.")
    elif delta < 0:
        st.success(f"최근 기록 대비 BMI가 {abs(delta):.2f} 감소했습니다.")
    else:
        st.info("최근 BMI 변화가 없습니다.")

# =======================
# 기록 테이블 & 삭제
# =======================
st.subheader("📋 BMI 기록 관리")

delete_ids = []

for _, row in user_df.iterrows():
    cols = st.columns([0.5, 2, 1, 1, 1, 1])
    checked = cols[0].checkbox("", key=f"del_{row['id']}")
    cols[1].write(row["date"])
    cols[2].write(row["height"])
    cols[3].write(row["weight"])
    cols[4].write(row["bmi"])
    cols[5].write(row["status"])

    if checked:
        delete_ids.append(row["id"])

if delete_ids:
    if st.button("🗑 선택 기록 삭제"):
        cursor.execute(
            f"DELETE FROM bmi_history WHERE id IN ({','.join('?' * len(delete_ids))})",
            delete_ids,
        )
        conn.commit()
        st.success("삭제 완료")
        st.rerun()


# =======================
st.subheader("🍽 추천 식단 가이드")

if plan_type == "감량":
    st.info(
        """
    🥗 **감량 식단 추천**
    - 아침: 삶은 달걀 2개 + 바나나
    - 점심: 현미밥 + 닭가슴살 + 나물
    - 저녁: 두부/생선 + 샐러드
    - 간식: 그릭요거트
    """
    )
elif plan_type == "유지":
    st.success(
        """
    🍚 **유지 식단 추천**
    - 아침: 토스트 + 계란
    - 점심: 일반 한식 (국/밥/단백질)
    - 저녁: 균형 잡힌 식사
    - 간식: 견과류
    """
    )
else:
    st.warning(
        """
    🍖 **증량 식단 추천**
    - 아침: 오트밀 + 우유
    - 점심: 밥 + 고기 + 반찬
    - 저녁: 단백질 위주
    - 간식: 고구마, 쉐이크
    """
    )
