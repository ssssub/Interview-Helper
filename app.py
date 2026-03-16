import streamlit as st
import google.generativeai as genai
import json
import datetime
import re
from typing import List, Dict

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

    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    .main { background-color: #F8FAFC; }

    .header-container {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        padding: 50px 0 30px 0; width: 100%;
    }
    .header-title {
        font-size: 2.8rem; font-weight: 700; color: #1E293B; margin-bottom: 10px; letter-spacing: -0.05rem;
    }
    .header-subtitle { font-size: 1.1rem; color: #64748B; font-weight: 400; }

    .stTextArea textarea {
        border-radius: 12px; border: 1px solid #E2E8F0; padding: 16px; font-size: 0.95rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: border-color 0.2s;
    }
    .stTextArea textarea:focus { border-color: #3B82F6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }

    .section-header { font-size: 1.2rem; font-weight: 600; color: #334155; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }

    .stButton { display: flex; justify-content: center; margin-top: 20px; }
    .stButton > button {
        width: 100%; background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: white; border: none; padding: 14px 24px; border-radius: 10px;
        font-weight: 500; font-size: 1.0rem; letter-spacing: 0.02rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: all 0.2s ease;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }

    .result-card {
        background-color: white; border-radius: 16px; padding: 30px;
        border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 20px;
    }
    .score-badge {
        background-color: #EFF6FF; color: #1D4ED8; padding: 8px 16px;
        border-radius: 20px; font-weight: 600; font-size: 0.9rem; display: inline-block; margin-bottom: 15px;
    }
    .small-metric-box {
        background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 16px; margin-top: 10px;
    }
    .keyword-chip {
        display: inline-block;
        padding: 6px 10px;
        margin: 4px 4px 0 0;
        border-radius: 999px;
        font-size: 0.85rem;
        background: #F1F5F9;
        color: #334155;
        border: 1px solid #E2E8F0;
    }
    .keyword-chip.hit {
        background: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
    }
    .keyword-chip.miss {
        background: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FECACA;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. API 키 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ API Key 오류: Streamlit Secrets에 GEMINI_API_KEY를 등록해주세요.")
    st.stop()


# ---------------------------
# 유틸 함수
# ---------------------------

def safe_json_loads(text: str) -> Dict:
    """
    모델 응답에서 ```json ... ``` 제거 후 JSON 파싱
    """
    cleaned = text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


def normalize_text(text: str) -> str:
    """
    비교용 텍스트 정규화
    """
    text = text.lower()
    text = re.sub(r"[\n\r\t]", " ", text)
    text = re.sub(r"[^\w가-힣\s/+-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_keyword_variants(keyword: str) -> List[str]:
    """
    하나의 키워드에 여러 표현이 섞여 있을 가능성을 고려
    예: "SQL / 데이터 추출", "Python(분석 자동화)", "커뮤니케이션 역량"
    """
    keyword = keyword.strip()
    variants = [keyword]

    # 괄호 제거 버전
    no_paren = re.sub(r"\(.*?\)", "", keyword).strip()
    if no_paren and no_paren not in variants:
        variants.append(no_paren)

    # / 로 분리
    slash_split = [k.strip() for k in re.split(r"/|,|·", no_paren) if k.strip()]
    variants.extend(slash_split)

    # 중복 제거
    dedup = []
    for v in variants:
        if v and v not in dedup:
            dedup.append(v)
    return dedup


def keyword_match(keyword: str, resume_text: str) -> bool:
    """
    키워드가 이력서에 있는지 비교
    - 완전 포함 우선
    - 여러 단어면 각 토큰이 대부분 포함되는지도 확인
    """
    norm_resume = normalize_text(resume_text)
    variants = split_keyword_variants(keyword)

    for variant in variants:
        norm_variant = normalize_text(variant)
        if not norm_variant:
            continue

        # 1) 완전 포함
        if norm_variant in norm_resume:
            return True

        # 2) 토큰 단위 부분 매칭
        tokens = [t for t in norm_variant.split() if len(t) >= 2]
        if len(tokens) >= 2:
            matched = sum(1 for t in tokens if t in norm_resume)
            # 토큰의 70% 이상 포함 시 매칭으로 간주
            if matched / len(tokens) >= 0.7:
                return True

    return False


def calculate_keyword_metrics(keywords: List[str], resume_text: str) -> Dict:
    """
    키워드 리스트에 대해 매칭 결과 계산
    """
    matched = []
    unmatched = []

    for kw in keywords:
        if keyword_match(kw, resume_text):
            matched.append(kw)
        else:
            unmatched.append(kw)

    total = len(keywords)
    score = round((len(matched) / total) * 100) if total > 0 else 0

    return {
        "total": total,
        "matched": matched,
        "unmatched": unmatched,
        "score": score
    }


def calculate_weighted_score(required_keywords: List[str], preferred_keywords: List[str], resume_text: str,
                             req_weight: float = 0.75, pref_weight: float = 0.25) -> Dict:
    """
    자격요건/우대사항 가중치 반영 최종 점수 계산
    """
    req_metrics = calculate_keyword_metrics(required_keywords, resume_text)
    pref_metrics = calculate_keyword_metrics(preferred_keywords, resume_text)

    final_score = round((req_metrics["score"] * req_weight) + (pref_metrics["score"] * pref_weight))

    return {
        "final_score": final_score,
        "required": req_metrics,
        "preferred": pref_metrics,
        "weights": {
            "required_weight": req_weight,
            "preferred_weight": pref_weight
        }
    }


def build_feedback(required_unmatched: List[str], preferred_unmatched: List[str]) -> str:
    """
    부족한 항목 기반 피드백 문장 생성
    """
    if not required_unmatched and not preferred_unmatched:
        return "자격요건과 우대사항이 전반적으로 잘 반영되어 있습니다. 실제 성과 수치와 구체적인 프로젝트 역할을 덧붙이면 설득력이 더 높아집니다."

    feedback_parts = []

    if required_unmatched:
        top_req = ", ".join(required_unmatched[:3])
        feedback_parts.append(f"우선 자격요건 측면에서 {top_req} 관련 경험을 더 명확히 드러내는 것이 중요합니다")

    if preferred_unmatched:
        top_pref = ", ".join(preferred_unmatched[:2])
        feedback_parts.append(f"추가로 우대사항인 {top_pref} 부분을 보완하면 경쟁력이 더 높아질 수 있습니다")

    return ". ".join(feedback_parts) + "."


def score_to_summary(score: int) -> str:
    """
    점수 요약 문장
    """
    if score >= 85:
        return "JD와의 정합성이 매우 높으며, 핵심 요구 역량이 이력서에 충분히 반영되어 있습니다."
    elif score >= 70:
        return "전반적으로 적합도가 높은 편이며, 일부 부족한 항목만 보완하면 더 경쟁력 있는 지원서가 됩니다."
    elif score >= 55:
        return "핵심 역량 일부는 부합하지만, 자격요건 중심으로 보완이 필요한 수준입니다."
    else:
        return "현재 기준으로는 JD와의 정합성이 높지 않아, 필수 역량 중심의 보완이 우선 필요합니다."


# ---------------------------
# 4. 헤더
# ---------------------------
st.markdown("""
    <div class="header-container">
        <div class="header-subtitle">AI 기반 면접관이 당신의 이력서 및 스펙과 공고를 분석하여 질문을 생성합니다.</div>
        <div class="header-title">Interview Master</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 5. 입력 섹션
left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.markdown('<div class="section-header">📄 채용 공고 (JD)</div>', unsafe_allow_html=True)
    jd_input = st.text_area(
        "jd_input",
        placeholder="지원하려는 공고 내용을 입력하세요.",
        height=400,
        label_visibility="collapsed"
    )

with right_col:
    st.markdown('<div class="section-header">👤 나의 이력서 / 스펙</div>', unsafe_allow_html=True)
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
        options=["부드러운 면접 (Soft)", "표준 면접 (Standard)", "압박 면접 (Pressure)"],
        value="표준 면접 (Standard)"
    )
    analyze_btn = st.button("AI 심층 분석 시작", use_container_width=True)

# 세션 스테이트 초기화
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None
if "log_saved" not in st.session_state:
    st.session_state["log_saved"] = False

# ---------------------------
# 7. AI 분석 로직
# ---------------------------
if analyze_btn:
    print(f"\n[{datetime.datetime.now()}] 🖱️ '분석 시작' 버튼 클릭됨", flush=True)

    if not jd_input or not resume_input:
        st.warning("⚠️ 정확한 분석을 위해 채용 공고와 이력서 내용을 모두 입력해주세요.")
    else:
        with st.status("🔍 AI 면접관이 서류를 검토하고 있습니다...", expanded=True) as status:
            try:
                # 모델 설정
                config_strict = {
                    "temperature": 0.0,
                    "top_p": 1,
                    "top_k": 1,
                }

                config_creative = {
                    "temperature": 0.8,
                }

                model_strict = genai.GenerativeModel(
                    "models/gemma-3-27b-it",
                    generation_config=config_strict
                )

                model_creative = genai.GenerativeModel(
                    "models/gemma-3-27b-it",
                    generation_config=config_creative
                )

                # [STEP 1] JD 구조화 및 키워드 추출
                print(f"[{datetime.datetime.now()}] 1️⃣ JD 구조화 및 키워드 추출 중...", flush=True)

                prompt_extract = f"""
                당신은 채용 공고를 구조화하는 HR 분석가입니다.

                아래 JD를 읽고 반드시 JSON만 출력하세요. 마크다운은 절대 포함하지 마세요.

                [JD]
                {jd_input}

                [지침]
                1. 직무명을 한국어로 짧게 분류하세요.
                2. JD에서 '자격요건(필수)' 키워드를 최대 8개 추출하세요.
                3. JD에서 '우대사항' 키워드를 최대 5개 추출하세요.
                4. 자격요건/우대사항이 명시적으로 구분되지 않더라도 문맥상 필수와 우대를 추론해 분리하세요.
                5. 각 키워드는 짧고 비교 가능한 형태로 작성하세요.
                6. 중복 키워드는 제거하세요.

                [출력 형식]
                {{
                    "job_category": "직무명",
                    "required_keywords": ["키워드1", "키워드2"],
                    "preferred_keywords": ["키워드1", "키워드2"]
                }}
                """

                res_extract = model_strict.generate_content(prompt_extract)
                extract_json = safe_json_loads(res_extract.text)

                required_keywords = extract_json.get("required_keywords", [])[:8]
                preferred_keywords = extract_json.get("preferred_keywords", [])[:5]
                job_category = extract_json.get("job_category", "직무 미상")

                # [STEP 2] Python에서 직접 점수 계산
                print(f"[{datetime.datetime.now()}] 2️⃣ 가중치 점수 계산 중...", flush=True)

                score_result = calculate_weighted_score(
                    required_keywords=required_keywords,
                    preferred_keywords=preferred_keywords,
                    resume_text=resume_input,
                    req_weight=0.75,
                    pref_weight=0.25
                )

                final_score = score_result["final_score"]
                req_score = score_result["required"]["score"]
                pref_score = score_result["preferred"]["score"]

                summary = score_to_summary(final_score)
                feedback = build_feedback(
                    score_result["required"]["unmatched"],
                    score_result["preferred"]["unmatched"]
                )

                # [STEP 3] 질문 생성
                print(f"[{datetime.datetime.now()}] 3️⃣ 면접 질문 생성 중...", flush=True)

                prompt_questions = f"""
                당신은 '{mode}' 스타일의 면접관입니다.

                아래 정보를 바탕으로 한국어 면접 질문 3개를 생성하세요.

                [분석 정보]
                직무: {job_category}
                최종 적합도 점수: {final_score}
                자격요건 매칭률: {req_score}
                우대사항 매칭률: {pref_score}
                매칭된 자격요건: {score_result["required"]["matched"]}
                부족한 자격요건: {score_result["required"]["unmatched"]}
                매칭된 우대사항: {score_result["preferred"]["matched"]}
                부족한 우대사항: {score_result["preferred"]["unmatched"]}

                [지침]
                1. 질문은 날카롭고 구체적으로 작성하세요.
                2. 부족한 자격요건과 실제 경험 검증이 드러나도록 하세요.
                3. 각 질문마다 '질문 의도'와 '답변 팁'을 포함하세요.
                4. 반드시 JSON만 출력하세요. 마크다운 금지.

                [출력 형식]
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

                res_questions = model_creative.generate_content(prompt_questions)
                questions_json = safe_json_loads(res_questions.text)

                final_result = {
                    "score": final_score,
                    "job_category": job_category,
                    "summary": summary,
                    "feedback": feedback,
                    "required_keywords": required_keywords,
                    "preferred_keywords": preferred_keywords,
                    "required_score": req_score,
                    "preferred_score": pref_score,
                    "required_matched": score_result["required"]["matched"],
                    "required_unmatched": score_result["required"]["unmatched"],
                    "preferred_matched": score_result["preferred"]["matched"],
                    "preferred_unmatched": score_result["preferred"]["unmatched"],
                    "questions": questions_json.get("questions", []),
                    "meta": {
                        "timestamp": str(datetime.datetime.now()),
                        "mode": mode,
                        "jd_len": len(jd_input),
                        "resume_len": len(resume_input),
                        "weights": {
                            "required": 0.75,
                            "preferred": 0.25
                        }
                    }
                }

                st.session_state["analysis_result"] = final_result
                st.session_state["log_saved"] = False

                status.update(label="✅ 분석 완료!", state="complete", expanded=False)

            except Exception as e:
                print(f"[{datetime.datetime.now()}] 🚨 오류 발생: {str(e)}", flush=True)
                st.error(f"오류가 발생했습니다: {str(e)}")
                st.stop()


# ---------------------------
# 결과 화면 출력
# ---------------------------
if st.session_state["analysis_result"]:
    result = st.session_state["analysis_result"]
    meta = result["meta"]

    if not st.session_state["log_saved"]:
        log_msg = (
            f"[{datetime.datetime.now()}] 📊 분석결과 | "
            f"직무: {result.get('job_category', 'Unknown')} | "
            f"점수: {result['score']} | "
            f"자격요건점수: {result['required_score']} | "
            f"우대사항점수: {result['preferred_score']} | "
            f"모드: {meta['mode']} | "
            f"글자수(J/R): {meta['jd_len']}/{meta['resume_len']} | "
            f"질문수: {len(result['questions'])}"
        )
        print(log_msg, flush=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 점수 카드
    st.markdown(f"""
    <div class="result-card" style="text-align: center;">
        <span class="score-badge">직무 적합도</span>
        <h1 style="color: #1E293B; font-size: 3.5rem; margin: 10px 0;">{result['score']}<span style="font-size: 1.5rem; color: #94A3B8;">/100</span></h1>
        <p style="font-size: 1.0rem; color: #64748B; margin-bottom: 5px;">분석 직무: {result.get('job_category', '직무 미상')}</p>
        <p style="font-size: 1.1rem; color: #475569;">{result['summary']}</p>
        <div style="background: #F1F5F9; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: left;">
            <strong style="color: #334155;">💡 보완 Tip:</strong> <span style="color: #475569;">{result['feedback']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 세부 점수
    detail_col1, detail_col2 = st.columns(2)

    with detail_col1:
        st.markdown("""
        <div class="small-metric-box">
            <h4 style="margin-bottom: 8px; color:#1E293B;">✅ 자격요건 매칭률</h4>
        </div>
        """, unsafe_allow_html=True)
        st.metric("자격요건", f"{result['required_score']}%")
        st.caption("가중치 75% 반영")

    with detail_col2:
        st.markdown("""
        <div class="small-metric-box">
            <h4 style="margin-bottom: 8px; color:#1E293B;">⭐ 우대사항 매칭률</h4>
        </div>
        """, unsafe_allow_html=True)
        st.metric("우대사항", f"{result['preferred_score']}%")
        st.caption("가중치 25% 반영")

    st.markdown("---")

    # 키워드 시각화
    kw_col1, kw_col2 = st.columns(2)

    with kw_col1:
        st.subheader("📌 자격요건 분석")
        st.markdown("**매칭된 항목**")
        if result["required_matched"]:
            st.markdown("".join([f'<span class="keyword-chip hit">{kw}</span>' for kw in result["required_matched"]]), unsafe_allow_html=True)
        else:
            st.caption("매칭된 자격요건이 없습니다.")

        st.markdown("**보완이 필요한 항목**")
        if result["required_unmatched"]:
            st.markdown("".join([f'<span class="keyword-chip miss">{kw}</span>' for kw in result["required_unmatched"]]), unsafe_allow_html=True)
        else:
            st.caption("모든 자격요건이 반영되었습니다.")

    with kw_col2:
        st.subheader("🌟 우대사항 분석")
        st.markdown("**매칭된 항목**")
        if result["preferred_matched"]:
            st.markdown("".join([f'<span class="keyword-chip hit">{kw}</span>' for kw in result["preferred_matched"]]), unsafe_allow_html=True)
        else:
            st.caption("매칭된 우대사항이 없습니다.")

        st.markdown("**추가로 어필 가능한 항목**")
        if result["preferred_unmatched"]:
            st.markdown("".join([f'<span class="keyword-chip miss">{kw}</span>' for kw in result["preferred_unmatched"]]), unsafe_allow_html=True)
        else:
            st.caption("우대사항도 전반적으로 잘 반영되었습니다.")

    st.markdown("---")

    st.subheader(f"📝 {meta['mode']} 스타일 예상 질문")

    for i, q in enumerate(result["questions"]):
        with st.expander(f"Q{i+1}. {q['q']}", expanded=True):
            st.markdown(f"**🎯 질문 의도:** {q['intent']}")
            st.info(f"**💡 답변 가이드:** {q['tip']}")

    # 만족도 및 의견 조사
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
            clean_comment = comment.replace('\n', ' ') if comment else "의견없음"

            full_log = (
                f"[{datetime.datetime.now()}] ⭐ 사용자피드백 | "
                f"만족도: {score}점 | "
                f"의견: {clean_comment} | "
                f"직무: {result.get('job_category')} | "
                f"점수: {result['score']} | "
                f"자격요건점수: {result['required_score']} | "
                f"우대사항점수: {result['preferred_score']} | "
                f"모드: {meta['mode']} | "
                f"JD: {meta['jd_len']}자 | "
                f"Resume: {meta['resume_len']}자"
            )
            print(full_log, flush=True)
            st.toast("서비스를 이용해주셔서 감사합니다!", icon="✅")
            st.session_state["log_saved"] = True

        for i in range(5):
            if cols[i].button(f"{emojis[i]} {i+1}점", use_container_width=True, key=f"rating_{i}"):
                save_feedback(i + 1, user_comment)
