import streamlit as st
import google.generativeai as genai

# [설정] 페이지 설정
st.set_page_config(page_title="Global AI Tutor", page_icon="🗣️", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "current_config" not in st.session_state:
    st.session_state.current_config = {"lang": None, "level": None, "topic": None}

with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    language = st.selectbox("Learning Language", ["English", "Japanese", "German"])
    level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
    topic = st.selectbox("Topic", ["Self-intro", "Travel", "Food", "Work", "Free Talk"])

    if st.button("🔄 Start New Session"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()


# [프롬프트 수정] 일본어의 경우 한자 읽기(후리가나) 지침 추가
def get_system_prompt(lang, level, topic):
    headers = {
        "English": {"corr": "💡 Correction", "next": "🗣️ Next Question"},
        "Japanese": {
            "corr": "💡 添削 (Correction)",
            "next": "🗣️ 次の質問 (Next Question)",
        },
        "German": {"corr": "💡 Korrektur", "next": "🗣️ Nächste Frage"},
    }
    h = headers[lang]

    # 일본어 전용 추가 지침
    jp_extra = ""
    if lang == "Japanese":
        jp_extra = """
        4. **Kanji Reading (Furiganas)**: For Japanese responses, always provide readings for difficult Kanji using parentheses, like this: 漢字(かんじ). 
        Especially for 'Beginner' level, provide readings for ALL Kanji.
        """

    return f"""
    You are a friendly {lang} teacher.
    Student Level: {level}
    Topic: {topic}
    
    Rules:
    1. Reply ONLY in {lang}.
    2. Format:
       [Your Response in {lang}]
       
       {h['corr']}: (If user made a mistake)
       
       {h['next']}: [Your follow-up question]
    
    3. Keep sentences appropriate for {level} level.
    {jp_extra}
    5. Use emojis to be friendly.
    """


st.title(f"🗣️ AI {language} Tutor")

if not api_key:
    st.warning("Please enter your Gemini API Key in the sidebar.")
    st.stop()

genai.configure(api_key=api_key)

if (
    st.session_state.chat_session is None
    or st.session_state.current_config["lang"] != language
):
    try:
        sys_instructions = get_system_prompt(language, level, topic)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash", system_instruction=sys_instructions
        )
        st.session_state.chat_session = model.start_chat(history=[])

        first_msg = f"Hi, I want to practice {language}. I'm at {level} level. Let's talk about {topic}."
        response = st.session_state.chat_session.send_message(first_msg)

        st.session_state.messages = [{"role": "assistant", "content": response.text}]
        st.session_state.current_config = {
            "lang": language,
            "level": level,
            "topic": topic,
        }
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat_session.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append(
                {"role": "assistant", "content": response.text}
            )
        except Exception as e:
            st.error(f"Failed to generate response: {e}")
