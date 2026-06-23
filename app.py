import streamlit as st
from google import genai
from google.genai import types
import json
import datetime
import textwrap
import html


# =========================
# 1. 페이지 기본 설정
# =========================
st.set_page_config(
    page_title="Interview Master | AI 면접 분석",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================
# 2. 디자인 CSS
# =========================
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


# =========================
# 3. Gemini API 설정
# =========================
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

except Exception:
    st.error("⚠️ API Key 오류: Streamlit Secrets에 GEMINI_API_KEY를 등록해주세요.")
    st.stop()


# =========================
# 4. 보조 함수
# =========================
def parse_json_response(response_text: str) -> dict:
    """
    Gemini 응답이 혹시 코드블록 형태로 와도
    JSON만 추출해서 읽도록 처리하는 함수.
    """
    cleaned_text = response_text.strip()

    cleaned_text = cleaned_text.replace("```json", "")
    cleaned_text = cleaned_text.replace("```", "")
    cleaned_text = cleaned_text.strip()

    return json.loads(cleaned_text)


def sanitize_text(value) -> str:
    """
    결과 카드 HTML 렌더링 시
    태그나 특수문자로 카드가 깨지는 것을 방지.
    """
    return html.escape(str(value if value is not None else ""))


# =========================
# 5. 헤더
# =========================
st.markdown("""
<div class="header-container">
    <div class="header-subtitle">
        AI 기반 면접관이 당신의 이력서 및 스펙과 공고를 분석하여 질문을 생성합니다.
    </div>
    <div class="header-title">Interview Master</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# =========================
# 6. 입력 섹션
# =========================
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


# =========================
# 7. 컨트롤 영역
# =========================
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


# =========================
# 8. 세션 상태 초기화
# =========================
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if "log_saved" not in st.session_state:
    st.session_state["log_saved"] = False


# =========================
# 9. AI 분석 로직
# =========================
if analyze_btn:
    print(
        f"\n[{datetime.datetime.now()}] 🖱️ 분석 시작 버튼 클릭",
        flush=True
    )

    if not jd_input.strip() or not resume_input.strip():
        st.warning("⚠️ 정확한 분석을 위해 채용 공고와 이력서 내용을 모두 입력해주세요.")

    else:
        with st.status(
            "🔍 AI 면접관이 서류를 검토하고 있습니다...",
            expanded=True
        ) as status:

            try:
                # -------------------------
                # STEP 1. 적합도 분석
                # -------------------------
                print(
                    f"[{datetime.datetime.now()}] 1️⃣ 적합도 분석 시작",
                    flush=True
                )

                prompt_score = f"""
당신은 냉정하고 객관적인 채용 평가자입니다.

아래 채용 공고와 이력서를 바탕으로 지원자의 직무 적합도를 평가하세요.

[채용 공고]
{jd_input}

[지원자 이력서]
{resume_input}

[평가 절차]
1. JD에서 필수 역량 키워드를 최대 10개 추출하세요.
2. 이력서에 해당 역량 또는 실질적으로 유사한 경험이 있는지 판단하세요.
3. 매칭 정도에 따라 직무 적합도 점수를 0~100점으로 평가하세요.
4. 매칭되는 경험이 부족하면 30~50점대도 적극적으로 부여하세요.
5. 직무 분류는 짧고 명확한 한국어 직무명으로 작성하세요.
6. 보완점은 JD에서 중요하지만 이력서에서 부족한 항목 중심으로 작성하세요.

[출력 조건]
- 생각 과정은 작성하지 마세요.
- 반드시 JSON만 반환하세요.
- 마크다운 코드블록은 사용하지 마세요.

{{
    "score": 0,
    "job_category": "직무명",
    "summary": "지원자에 대한 한두 문장 평가",
    "feedback": "보완이 필요한 역량과 구체적 보완 방향"
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

                json_score = parse_json_response(response_score.text)

                # 점수 방어 처리
                try:
                    score_value = int(json_score.get("score", 0))
                    json_score["score"] = max(0, min(score_value, 100))
                except Exception:
                    json_score["score"] = 0

                # -------------------------
                # STEP 2. 면접 질문 생성
                # -------------------------
                print(
                    f"[{datetime.datetime.now()}] 2️⃣ 면접 질문 생성 시작",
                    flush=True
                )

                prompt_questions = f"""
당신은 '{mode}' 스타일의 면접관입니다.

[지원 직무]
{json_score.get("job_category", "직무 미상")}

[채용 공고]
{jd_input}

[지원자 이력서]
{resume_input}

위 정보를 바탕으로 실제 면접에서 활용할 수 있는 면접 질문 3개를 만드세요.

질문은 단순히 이력서를 읽는 수준이 아니라,
지원자의 경험, 직무 이해도, 문제 해결 방식, 실무 적합성을 검증할 수 있어야 합니다.

[출력 조건]
- 모든 내용은 자연스러운 한국어로 작성하세요.
- 반드시 JSON만 반환하세요.
- 마크다운 코드블록은 사용하지 마세요.

{{
    "questions": [
        {{
            "q": "면접 질문",
            "intent": "이 질문을 통해 확인하려는 역량",
            "tip": "답변할 때 강조해야 할 포인트"
        }},
        {{
            "q": "면접 질문",
            "intent": "이 질문을 통해 확인하려는 역량",
            "tip": "답변할 때 강조해야 할 포인트"
        }},
        {{
            "q": "면접 질문",
            "intent": "이 질문을 통해 확인하려는 역량",
            "tip": "답변할 때 강조해야 할 포인트"
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

                json_questions = parse_json_response(response_questions.text)

                # -------------------------
                # STEP 3. 결과 합치기
                # -------------------------
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
                st.error("⚠️ AI 응답 형식이 올바르지 않습니다. 다시 시도해주세요.")

            except Exception as e:
                print(
                    f"[{datetime.datetime.now()}] 🚨 오류 발생: {str(e)}",
                    flush=True
                )

                st.error(f"오류가 발생했습니다: {str(e)}")


# =========================
# 10. 분석 결과 출력
# =========================
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

    # HTML 특수문자 처리
    score = sanitize_text(result.get("score", 0))
    job_category = sanitize_text(result.get("job_category", "직무 미상"))
    summary = sanitize_text(result.get("summary", ""))
    feedback = sanitize_text(result.get("feedback", ""))

    # 들여쓰기 제거 후 HTML 렌더링
    result_card_html = textwrap.dedent(f"""
    <div class="result-card" style="text-align: center;">
        <span class="score-badge">직무 적합도</span>

        <h1 style="color: #1E293B; font-size: 3.5rem; margin: 10px 0;">
            {score}
            <span style="font-size: 1.5rem; color: #94A3B8;">/100</span>
        </h1>

        <p style="font-size: 1.0rem; color: #64748B; margin-bottom: 5px;">
            분석 직무: {job_category}
        </p>

        <p style="font-size: 1.1rem; color: #475569;">
            {summary}
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
                {feedback}
            </span>
        </div>
    </div>
    """).strip()

    st.markdown(result_card_html, unsafe_allow_html=True)

    st.subheader(f"📝 {meta['mode']} 스타일 예상 질문")

    questions = result.get("questions", [])

    for i, question in enumerate(questions):
        question_text = question.get("q", "질문을 불러오지 못했습니다.")
        intent = question.get("intent", "")
        tip = question.get("tip", "")

        with st.expander(f"Q{i + 1}. {question_text}", expanded=True):
            st.markdown(f"**🎯 질문 의도:** {intent}")
            st.info(f"**💡 답변 가이드:** {tip}")


    # =========================
    # 11. 만족도 조사
    # =========================
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

    def save_feedback(score_value, comment):
        clean_comment = (
            comment.replace("\n", " ")
            if comment
            else "의견없음"
        )

        full_log = (
            f"[{datetime.datetime.now()}] ⭐ 사용자피드백 | "
            f"만족도: {score_value}점 | "
            f"의견: {clean_comment} | "
            f"직무: {result.get('job_category')} | "
            f"적합도: {result.get('score')} | "
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

    with button_container:
        cols = st.columns(5)
        emojis = ["😡", "🙁", "😐", "🙂", "😍"]

        for i in range(5):
            if cols[i].button(
                f"{emojis[i]} {i + 1}점",
                use_container_width=True,
                key=f"rating_{i}"
            ):
                save_feedback(i + 1, user_comment)
