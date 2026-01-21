import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np


# 1. 데이터 로드 및 전처리 (인코딩 설정 추가)
@st.cache_data
def load_data():
    try:
        # 공공기관 데이터는 보통 'cp949' 또는 'euc-kr' 인코딩을 사용합니다.
        df = pd.read_csv("산림청 10년간 산사태 피해현황.csv", encoding="cp949")
    except UnicodeDecodeError:
        # 만약 cp949로 안될 경우 euc-kr로 시도
        df = pd.read_csv("산림청 10년간 산사태 피해현황.csv", encoding="euc-kr")

    # 데이터 전처리
    df = df.set_index("시군(단위 : ha)")
    df = df.fillna(0)  # 결측치 0 처리

    # 컬럼명에서 '년' 제거 후 숫자로 변환 (예: '2010년' -> 2010)
    df.columns = [int(str(col).replace("년", "")) for col in df.columns]
    return df


# 대시보드 레이아웃 설정
st.set_page_config(page_title="산사태 분석 대시보드", layout="wide")

try:
    df = load_data()
    yearly_total = df.sum()
    city_total = df.sum(axis=1).sort_values(ascending=False)

    # --- 대시보드 메인 ---
    st.title("🌲 전남 산사태 피해 분석 & 예측 대시보드")
    st.markdown(
        "2010년부터 2019년까지의 산림청 산사태 피해 데이터를 시각화하고 미래를 예측합니다."
    )

    # 탭 구성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📈 연도별 추이",
            "📊 지역별 비교",
            "🍕 피해 비중",
            "📋 데이터 요약",
            "🔮 미래 예측",
            "🔍 변동성 분석",
        ]
    )

    # [분석 1] 연도별 추이
    with tab1:
        st.subheader("연도별 피해 면적 변화 (2010-2019)")
        fig1 = px.line(
            x=yearly_total.index,
            y=yearly_total.values,
            labels={"x": "연도", "y": "피해 면적(ha)"},
            markers=True,
            line_shape="linear",
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.info(
            "2011년에 대규모 피해가 발생한 이후 점진적으로 감소하거나 낮은 수준을 유지하는 경향을 보입니다."
        )

    # [분석 2] 지역별 비교
    with tab2:
        st.subheader("시군별 누적 피해 면적 (Top 10)")
        top_cities = city_total.head(10)
        fig2 = px.bar(
            x=top_cities.index,
            y=top_cities.values,
            labels={"x": "지역명", "y": "누적 면적(ha)"},
            color=top_cities.values,
            color_continuous_scale="Reds",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # [분석 3] 상위 지역 비중
    with tab3:
        st.subheader("피해 상위 5개 지역의 비중")
        top5 = city_total.head(5)
        fig3 = px.pie(
            values=top5.values,
            names=top5.index,
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # [분석 4] 데이터 요약
    with tab4:
        st.subheader("시군별 상세 통계 및 데이터")
        col1, col2, col3 = st.columns(3)
        col1.metric("총 피해 면적", f"{city_total.sum():.2f} ha")
        col2.metric(
            "최대 피해 지역", f"{city_total.idxmax()}", f"{city_total.max():.2f} ha"
        )
        col3.metric("기록된 시군 수", f"{len(df)}개")

        st.dataframe(df.style.background_gradient(cmap="YlOrRd", axis=None))

    # [예측 탭] 미래 피해 예측
    with tab5:
        st.subheader("🔮 향후 5년 산사태 피해 면적 예측")
        st.write(
            "선형 회귀 알고리즘을 사용하여 향후 발생 가능성이 있는 피해 규모를 추정합니다."
        )

        # 선형 회귀 계산 (Numpy 사용)
        x_years = yearly_total.index.values
        y_values = yearly_total.values
        slope, intercept = np.polyfit(x_years, y_values, 1)

        # 2020~2024 예측
        future_years = np.array(range(2020, 2025))
        future_preds = slope * future_years + intercept
        future_preds = np.maximum(0, future_preds)  # 음수 방지

        res_df = pd.DataFrame({"연도": future_years, "예측 피해(ha)": future_preds})

        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("#### 예측 결과")
            st.table(res_df.style.format({"예측 피해(ha)": "{:.2f}"}))
        with c2:
            all_years = np.append(x_years, future_years)
            all_vals = np.append(y_values, future_preds)
            fig5 = px.line(
                x=all_years,
                y=all_vals,
                labels={"x": "연도", "y": "피해 면적(ha)"},
                title="과거 실적 및 향후 예측 추이",
                markers=True,
            )
            # 예측 영역 강조
            fig5.add_vrect(
                x0=2019.5,
                x1=2024.5,
                fillcolor="orange",
                opacity=0.1,
                annotation_text="예측 구간",
                annotation_position="top left",
            )
            st.plotly_chart(fig5, use_container_width=True)
    # 기존 탭 구성에 "🔍 변동성 분석" 추가
    # tab1, tab2, tab3, tab4, tab5 = st.tabs([...]) 부분에 추가

    with tab6:  # 상세 데이터 탭 대신 혹은 추가 탭으로 사용
        st.subheader("⚠️ 지역별 피해 변동성(Risk Stability) 분석")
        st.write(
            "표준편차가 높을수록 특정 시기에 대규모 피해가 집중되는 '기습형 위험 지역'임을 의미합니다."
        )

        # 변동성(표준편차) 계산
        volatility = df.std(axis=1).sort_values(ascending=False).head(10)

        # 평균 대비 변동성 파악을 위한 데이터프레임 생성
        analysis_df = pd.DataFrame(
            {
                "평균 피해(ha)": df.mean(axis=1),
                "변동성(표준편차)": df.std(axis=1),
                "최대 피해 기록": df.max(axis=1),
            }
        ).loc[volatility.index]

        # 시각화 1: 변동성 바 차트
        fig_vol = px.bar(
            analysis_df,
            x=analysis_df.index,
            y="변동성(표준편차)",
            color="변동성(표준편차)",
            title="시군별 피해 변동성 순위 (Top 10)",
            color_continuous_scale="OrRd",
        )
        st.plotly_chart(fig_vol, use_container_width=True)

        # 시각화 2: 평균 vs 변동성 산점도 (위험 지표)
        st.write("#### 📍 피해 규모와 예측 불가능성(변동성)의 관계")
        fig_scatter = px.scatter(
            analysis_df,
            x="평균 피해(ha)",
            y="변동성(표준편차)",
            size="최대 피해 기록",
            text=analysis_df.index,
            color="변동성(표준편차)",
            labels={"x": "10년 평균 피해량", "y": "변동성 (표준편차)"},
        )
        fig_scatter.update_traces(textposition="top center")
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.info(
            """
        **💡 분석 결과 해석:**
        - 우측 상단에 위치한 지역(광양 등)은 **평균 피해도 크고 변동성도 매우 커서** 집중 관리가 시급한 지역입니다.
        - 좌측 하단에 모여있는 지역들은 상대적으로 산사태 발생이 적거나 일정합니다.
        """
        )

except FileNotFoundError:
    st.error(
        "파일을 찾을 수 없습니다. CSV 파일이 파이썬 스크립트와 같은 폴더에 있는지 확인해주세요."
    )
except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
