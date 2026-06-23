
import streamlit as st
from google import genai
from google.genai import types
import json
import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="Interview Master | AI 면접 분석",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 디자인 CSS
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
    }

    .main {
        background-color: #F8FAFC;
    }

    .header-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 50px 0 30px 0;
        width: 100%;
    }

    .header-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 10px;
        letter-spacing: -0.05rem;
    }

    .header-subtitle {
        font-size: 1.1rem;
        color: #64748B;
        font-weight: 400;
    }

    .stTextArea textarea {
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        padding: 16px;
        font-size: 0.95rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: border-color 0.2s;
    }

    .stTextArea textarea:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .stButton {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }

    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: white;
        border: none;
        padding: 14px 24px;
        border-radius: 10px;
        font-weight: 500;
        font-size: 1rem;
        letter-spacing: 0.02rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    .result-card {
        background-color: white;
        border-radius: 16px;
        padding: 30px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }

    .score-badge {
        background-color: #EFF6FF;
        color: #1D4ED8;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Gemini API 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

except Exception:
    st.error("⚠️ API Key 오류: Streamlit Secrets에 GEMINI_API_KEY를 등록해주세요.")
    st.stop()

# 4. 헤더
st.markdown("""
    <div class="header-container">
        <div class="header-subtitle">
            AI 기반 면접관이 당신의 이력서 및 스펙과 공고를 분석하여 질문을 생성합니다.
        </div>
        <div class="header-title">Interview Master</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# 5. 입력 섹션
left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.markdown(
        '<div class="section-header">📄 채용 공고 (JD)</div>',
        unsafe_allow_html=True
    )
    jd_input = st.text_area(
        "jd_input",
        placeholder="지원하려는 공고 내용을 입력하세요.",
        height=400,
        label_visibility="collapsed"
    )

with right_col:
    st.markdown(
        '<div class="section-header">👤 나의 이력서 / 스펙</div>',
        unsafe_allow_html=True
    )
    resume_input = st.text_area(
        "resume_input",
        placeholder="이력서 또는 스펙을 입력하세요.",
        height=400,
        label_visibility="collapsed"
    )

# 6. 컨트롤 섹션
st.markdown("<br>", unsafe_allow_html=True)

_, center_col, _ = st.columns([1, 2, 1])

with center_col:
    mode = st.select_slider(
        "면접관 스타일을 선택하세요",
        options=[
            "부드러운 면접 (Soft)",
            "표준 면접 (Standard)",
            "압박 면접 (Pressure)"
        ],
        value="표준 면접 (Standard)"
    )

    analyze_btn = st.button(
        "AI 심층 분석 시작",
        use_container_width=True
    )

# 7. 세션 스테이트 초기화
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if "log_saved" not in st.session_state:
    st.session_state["log_saved"] = False

# 8. AI 분석 로직
if analyze_btn:
    print(
        f"\n[{datetime.datetime.now()}] 🖱️ '분석 시작' 버튼 클릭됨",
        flush=True
    )

    if not jd_input or not resume_input:
        st.warning("⚠️ 정확한 분석을 위해 채용 공고와 이력서 내용을 모두 입력해주세요.")

    else:
        with st.status(
            "🔍 AI 면접관이 서류를 검토하고 있습니다...",
            expanded=True
        ) as status:

            try:
                # STEP 1. 적합도 점수 + 직무 분류
                print(
                    f"[{datetime.datetime.now()}] 1️⃣ 직무 적합도 및 분류 분석 중...",
                    flush=True
                )

                prompt_score = f"""
당신은 냉정한 채용 평가자입니다.

아래 [채점 절차]를 엄격히 따르세요.

[입력 데이터]
JD:
{jd_input}

이력서:
{resume_input}

[채점 절차]
1. JD에서 필수 역량 키워드를 최대 10개 추출하세요.
2. 이력서에 해당 키워드 또는 실질적으로 동등한 경험이 있는지 판단하세요.
3. 매칭된 키워드 수 / 전체 핵심 키워드 수 × 100으로 점수를 산출하세요.
4. 점수는 10점 단위가 아니라 계산값에 가까운 정수로 반환하세요.
5. 직무 분류는 한국어로 짧게 정의하세요.
6. 보완점은 매칭되지 않은 JD 핵심 역량 중심으로 작성하세요.

[출력 조건]
- 생각 과정은 출력하지 마세요.
- 반드시 JSON만 반환하세요.
- 마크다운 코드블록은 사용하지 마세요.

{{
    "score": 0,
    "job_category": "직무명",
    "summary": "평가 요약",
    "feedback": "매칭되지 않은 핵심 키워드 위주의 보완점"
}}
"""

                response_score = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_score,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        top_p=1.0,
                        top_k=1,
                        response_mime_type="application/json"
                    )
                )

                text_score = response_score.text.strip()
                json_score = json.loads(text_score)

                # STEP 2. 면접 질문 생성
                print(
                    f"[{datetime.datetime.now()}] 2️⃣ 면접 질문 생성 중...",
                    flush=True
                )

                prompt_questions = f"""
당신은 '{mode}' 스타일의 면접관입니다.

[지원 직무]
{json_score["job_category"]}

[채용 공고]
{jd_input}

[지원자 이력서]
{resume_input}

위 내용을 바탕으로 해당 지원자에게 실제 면접에서 할 법한 날카로운 질문 3개를 생성하세요.

각 질문에는 아래 내용을 포함하세요.
- q: 면접 질문
- intent: 이 질문을 하는 면접관의 의도
- tip: 답변 방향 및 보완 팁

모든 내용은 자연스러운 한국어로 작성하세요.

[출력 조건]
- 반드시 JSON만 반환하세요.
- 마크다운 코드블록은 사용하지 마세요.

{{
    "questions": [
        {{
            "q": "질문 내용",
            "intent": "질문 의도",
            "tip": "답변 팁"
        }}
    ]
}}
"""

                response_questions = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt_questions,
                    config=types.GenerateContentConfig(
                        temperature=0.9,
                        response_mime_type="application/json"
                    )
                )

                text_questions = response_questions.text.strip()
                json_questions = json.loads(text_questions)

                # STEP 3. 결과 저장
                final_result = {
                    **json_score,
                    **json_questions
                }

                final_result["meta"] = {
                    "timestamp": str(datetime.datetime.now()),
                    "mode": mode,
                    "jd_len": len(jd_input),
                    "resume_len": len(resume_input)
                }

                st.session_state["analysis_result"] = final_result
                st.session_state["log_saved"] = False

                status.update(
                    label="✅ 분석 완료!",
                    state="complete",
                    expanded=False
                )

            except json.JSONDecodeError:
                st.error("⚠️ AI 응답을 JSON으로 읽지 못했습니다. 다시 시도해주세요.")

            except Exception as e:
                print(
                    f"[{datetime.datetime.now()}] 🚨 오류 발생: {str(e)}",
                    flush=True
                )
                st.error(f"오류가 발생했습니다: {str(e)}")

# 9. 결과 화면 출력
if st.session_state["analysis_result"]:
    result = st.session_state["analysis_result"]
    meta = result["meta"]

    if not st.session_state["log_saved"]:
        log_msg = (
            f"[{datetime.datetime.now()}] 📊 분석결과 | "
            f"직무: {result.get('job_category', 'Unknown')} | "
            f"점수: {result.get('score', 0)} | "
            f"모드: {meta['mode']} | "
            f"글자수(J/R): {meta['jd_len']}/{meta['resume_len']} | "
            f"질문수: {len(result.get('questions', []))}"
        )
        print(log_msg, flush=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="result-card" style="text-align: center;">
        <span class="score-badge">직무 적합도</span>
        <h1 style="color: #1E293B; font-size: 3.5rem; margin: 10px 0;">
            {result.get("score", 0)}
            <span style="font-size: 1.5rem; color: #94A3B8;">/100</span>
        </h1>

        <p style="font-size: 1.0rem; color: #64748B; margin-bottom: 5px;">
            분석 직무: {result.get("job_category", "직무 미상")}
        </p>

        <p style="font-size: 1.1rem; color: #475569;">
            {result.get("summary", "")}
        </p>

        <div style="
            background: #F1F5F9;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            text-align: left;
        ">
            <strong style="color: #334155;">💡 보완 Tip:</strong>
            <span style="color: #475569;">
                {result.get("feedback", "")}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader(f"📝 {meta['mode']} 스타일 예상 질문")

    for i, q in enumerate(result.get("questions", [])):
        with st.expander(f"Q{i + 1}. {q.get('q', '')}", expanded=True):
            st.markdown(f"**🎯 질문 의도:** {q.get('intent', '')}")
            st.info(f"**💡 답변 가이드:** {q.get('tip', '')}")

    # 10. 만족도 및 의견 조사
    st.markdown("---")
    st.markdown("#### 💬 서비스가 도움이 되셨나요?")
    st.caption("서비스 개선을 위해 의견을 남겨주세요.")

    button_container = st.container()
    feedback_container = st.container()

    with feedback_container:
        user_comment = st.text_area(
            "feedback_text",
            placeholder="자유롭게 의견을 남겨주세요. (작성 후 위 점수 버튼을 눌러주세요)",
            height=80,
            label_visibility="collapsed"
        )

    with button_container:
        cols = st.columns(5)
        emojis = ["😡", "🙁", "😐", "🙂", "😍"]

        def save_feedback(score, comment):
            clean_comment = (
                comment.replace("\n", " ")
                if comment
                else "의견없음"
            )

            full_log = (
                f"[{datetime.datetime.now()}] ⭐ 사용자피드백 | "
                f"만족도: {score}점 | "
                f"의견: {clean_comment} | "
                f"직무: {result.get('job_category')} | "
                f"점수: {result.get('score')} | "
                f"모드: {meta['mode']} | "
                f"JD: {meta['jd_len']}자 | "
                f"Resume: {meta['resume_len']}자"
            )

            print(full_log, flush=True)

            st.toast(
                "서비스를 이용해주셔서 감사합니다!",
                icon="✅"
            )

            st.session_state["log_saved"] = True

        for i in range(5):
            if cols[i].button(
                f"{emojis[i]} {i + 1}점",
                use_container_width=True,
                key=f"rating_{i}"
            ):
                save_feedback(i + 1, user_comment)
