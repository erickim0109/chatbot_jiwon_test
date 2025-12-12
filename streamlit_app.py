import streamlit as st
from openai import OpenAI

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "간단한 챗봇 데모입니다. OpenAI API 키가 필요합니다."
)

# Sidebar: model settings inside an expander so it can be collapsed.
with st.sidebar.expander("모델 및 모드 설정 (접기/펼치기)", expanded=False):
    model = st.selectbox(
        "모델 선택",
        options=["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"],
        index=2,
        help="테스트할 모델을 선택하세요."
    )

    # Mode presets for elementary use-case
    mode = st.radio(
        "모드 선택",
        options=["개념 유지 코치", "감정 코치"],
        index=0,
        help="학습(개념 설명/교정)과 정서 지원(감정 코칭) 중 하나를 선택하세요."
    )

    grade = st.selectbox(
        "학년 선택",
        options=["1학년", "2학년", "3학년", "4학년", "5학년", "6학년"],
        index=2,
        help="대상 학년을 선택하면 답변 톤과 예시 수준을 조절합니다."
    )

    # Allow user to edit or preview the generated system prompt
    system_prompt = st.text_area(
        "시스템 프롬프트 (수정 가능)",
        value="You are a helpful assistant.",
        key="system_prompt",
        help="시스템 역할(assistant의 동작 지침)을 설정합니다. 모드와 학년에 맞는 기본 프롬프트가 자동으로 생성됩니다.",
        height=140,
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.5,
        value=0.7,
        step=0.01,
        help="출력의 창의성 정도를 조절합니다(낮을수록 결정적).",
    )

    max_tokens = st.slider(
        "Max Tokens",
        min_value=50,
        max_value=4000,
        value=512,
        step=1,
        help="응답에 허용할 최대 토큰 수입니다.",
    )

    safe_mode = st.checkbox(
        "정서 지원 시 안전 모드 활성화",
        value=True,
        help="감정 관련 질문에 대해 비응급 안내와 도움 요청 권유(교사/보호자/긴급전화)를 자동으로 포함합니다."
    )

    # Accessibility: font size
    font_choice = st.selectbox(
        "글꼴 크기",
        options=["작게", "보통", "크게"],
        index=1,
        help="챗 메시지의 글자 크기를 조절합니다."
    )

    # Buttons: reset prompt and clear conversation
    if st.button("시스템 프롬프트 초기화"):
        st.session_state["system_prompt"] = ""
        st.experimental_rerun()

    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.experimental_rerun()

# Ask user for their OpenAI API key via `st.text_input`.
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("OpenAI API 키를 입력해 주세요.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Helper to send a user prompt and stream the assistant response.
    def send_and_stream(user_prompt: str):
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        # Build system prompt template if user didn't customize it.
        default_system_prompt = None
        current_system = st.session_state.get("system_prompt", "")
        if (not current_system) or current_system.strip() == "You are a helpful assistant.":
            if mode == "개념 유지 코치":
                default_system_prompt = (
                    f"You are an elementary school 'Concept Keeper' tutor for {grade}. "
                    "When a student asks about any school concept, explain clearly using short sentences, "
                    "simple words appropriate for the selected grade, step-by-step examples, and quick checks "
                    "(1-2 simple questions) to confirm understanding. If the student shows a misconception, gently correct it and provide a short practice exercise. "
                    "Be encouraging and positive. Keep replies concise and use age-appropriate analogies."
                )
            else:
                default_system_prompt = (
                    f"You are an elementary-friendly emotional coach for {grade}. "
                    "When a student shares feelings or problems (friendship, study, health), respond with empathy, "
                    "validate feelings, offer simple coping steps and actionable suggestions (talk to teacher/parent, breathe, small steps). "
                    "Avoid professional medical or legal advice. If the student mentions harm to self or others or an emergency, "
                    "clearly instruct them to seek immediate help from a trusted adult or emergency services."
                )

        final_system = current_system if (current_system and current_system.strip() and current_system.strip() != "You are a helpful assistant.") else default_system_prompt

        api_messages = []
        if final_system:
            api_messages.append({"role": "system", "content": final_system})

        if mode == "감정 코치" and safe_mode:
            safety_note = (
                "Note for students: I am a helpful guide but not a professional. "
                "If this is an emergency or you feel at risk, please contact a trusted adult or emergency services immediately."
            )
            api_messages.append({"role": "system", "content": safety_note})

        api_messages.extend(
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        )

        stream = client.chat.completions.create(
            model=model,
            messages=api_messages,
            temperature=float(temperature),
            max_tokens=int(max_tokens),
            stream=True,
        )

        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Initialize session state for messages.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display sample questions for quick testing
    if mode == "개념 유지 코치":
        sample_questions = [
            "중력은 뭐예요?",
            "분수는 어떻게 더해요?",
            "태양계에는 어떤 행성들이 있어요?",
        ]
    else:
        sample_questions = [
            "친구가 저를 무시해요. 어떻게 해야 하나요?",
            "시험 공부가 너무 어려워요. 팁이 있을까요?",
            "잠이 잘 안 와요. 어떻게 하면 좋을까요?",
        ]

    st.write("**예시 질문 (버튼 클릭 시 자동 전송)**")
    cols = st.columns(len(sample_questions))
    for i, q in enumerate(sample_questions):
        if cols[i].button(q):
            send_and_stream(q)

    # Display the existing chat messages with adjustable font size.
    size_map = {"작게": 14, "보통": 18, "크게": 22}
    chosen_size = size_map.get(st.session_state.get("font_choice", font_choice), 18)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            content = message["content"]
            styled = f"<div style='font-size: {chosen_size}px; line-height:1.4'>{content}</div>"
            st.markdown(styled, unsafe_allow_html=True)
    # Chat input. When user sends a message, call helper.
    if prompt := st.chat_input("메시지를 입력하세요..."):
        send_and_stream(prompt)
