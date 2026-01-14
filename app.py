import streamlit as st
import google.generativeai as genai
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
    </style>
    """, unsafe_allow_html=True)

# 3. API 키 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ API Key 오류: Streamlit Secrets에 GEMINI_API_KEY를 등록해주세요.")
    st.stop()

# 4. 헤더
st.markdown("""
    <div class="header-container">
        <div class="header-title">Interview Master</div>
        <div class="header-subtitle">AI 기반 면접관이 당신의 이력서와 공고를 분석하여 질문을 생성합니다</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 5. 입력 섹션
left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.markdown('<div class="section-header">📄 채용 공고 (JD)</div>', unsafe_allow_html=True)
    jd_input = st.text_area("jd_input", placeholder="지원하려는 공고 내용을 입력하세요.", height=400, label_visibility="collapsed")

with right_col:
    st.markdown('<div class="section-header">👤 나의 이력서 / 경험</div>', unsafe_allow_html=True)
    resume_input = st.text_area("resume_input", placeholder="이력서 또는 경험을 입력하세요.", height=400, label_visibility="collapsed")

# 6. 컨트롤 섹션
st.markdown("<br>", unsafe_allow_html=True)
_, center_col, _ = st.columns([1, 2, 1])

with center_col:
    mode = st.select_slider(
        "면접관 스타일을 선택하세요",
        options=["부드러운 면접 (Soft)", "표준 면접 (Standard)", "압박 면접 (Pressure)"],
        value="표준 면접 (Standard)"
    )
    analyze_btn = st.button("AI 심층 분석 시작")

# 7. AI 분석 로직

# [필수] 세션 스테이트 초기화 (결과 유지를 위해 필요)
if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None
if 'log_saved' not in st.session_state:
    st.session_state['log_saved'] = False

# 분석 버튼 클릭 시
if analyze_btn:
    print(f"\n[{datetime.datetime.now()}] 🖱️ '분석 시작' 버튼 클릭됨", flush=True)

    if not jd_input or not resume_input:
        st.warning("⚠️ 정확한 분석을 위해 채용 공고와 이력서 내용을 모두 입력해주세요.")
    else:
        with st.status("🔍 AI 면접관이 서류를 검토하고 있습니다...", expanded=True) as status:
            try:
                # [STEP 1] 점수 채점 + 직무 분류 (직무 분류 기능 추가됨)
                print(f"[{datetime.datetime.now()}] 1️⃣ 직무 적합도 및 분류 분석 중...", flush=True)
                
                config_strict = {
                    "temperature": 0.0, 
                    "top_p": 1, 
                    "top_k": 1, 
                    "response_mime_type": "application/json",
                }
                model_strict = genai.GenerativeModel('models/gemini-2.5-flash', generation_config=config_strict)
                
                # 프롬프트에 'job_category' 추출 요청 추가
                prompt_score = f"""
                당신은 엄격한 채점 알고리즘입니다. 
                
                [입력 데이터] 
                JD: {jd_input}
                이력서: {resume_input}
                
                [지시사항]
                1. JD를 분석하여 '직무 분류(job_category)'를 단답형으로 정의하세요. (예: 백엔드 개발, 영업 관리, 콘텐츠 마케팅)
                2. [채점 기준]에 따라 기계적으로 점수를 계산하세요.
                   - JD 핵심 키워드 매칭률(%)을 정수로 환산.
                   - 동일 입력값 = 동일 점수 (필수).

                JSON 형식: {{ "score": 숫자, "job_category": "직무명", "summary": "3줄 요약", "feedback": "핵심 보완점" }}
                """
                
                res_score = model_strict.generate_content(prompt_score)
                json_score = json.loads(res_score.text)
                
                
                # [STEP 2] 질문 생성
                print(f"[{datetime.datetime.now()}] 2️⃣ 면접 질문 생성 중...", flush=True)
                
                config_creative = {
                    "temperature": 1.0, 
                    "response_mime_type": "application/json",
                }
                model_creative = genai.GenerativeModel('models/gemini-2.5-flash', generation_config=config_creative)
                
                prompt_questions = f"""
                당신은 '{mode}' 스타일의 면접관입니다.
                직무: {json_score['job_category']}
                
                지원자 정보를 바탕으로 창의적이고 날카로운 면접 질문 3가지를 생성하세요.
                
                JSON 형식: {{ "questions": [ {{ "q": "질문", "intent": "의도", "tip": "팁" }}, ... ] }}
                """
                
                res_questions = model_creative.generate_content(prompt_questions)
                json_questions = json.loads(res_questions.text)
                
                
                # [STEP 3] 결과 합치기 및 세션 저장
                final_result = {**json_score, **json_questions}
                
                # 메타 데이터 추가 (로그용)
                final_result['meta'] = {
                    'timestamp': str(datetime.datetime.now()),
                    'mode': mode,
                    'jd_len': len(jd_input),
                    'resume_len': len(resume_input)
                }
                
                # 세션에 결과 저장 (화면 리로드를 위해)
                st.session_state['analysis_result'] = final_result
                st.session_state['log_saved'] = False # 아직 만족도 평가 안 함
                
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)

            except Exception as e:
                print(f"[{datetime.datetime.now()}] 🚨 오류 발생: {str(e)}", flush=True)
                st.error(f"오류가 발생했습니다: {str(e)}")
                st.stop()

# --- 결과 화면 출력 (세션에 데이터가 있을 경우에만 표시) ---
if st.session_state['analysis_result']:
    result = st.session_state['analysis_result']
    meta = result['meta']
    
    # 1차 로그 출력 (만족도 평가 전, 기본 데이터 로깅)
    # 사용자가 만족도를 안 누르고 나갈 수도 있으므로 여기서 기본 로그는 남깁니다.
    if not st.session_state['log_saved']:
        log_msg = (
            f"[{datetime.datetime.now()}] 📊 분석결과 | "
            f"직무: {result.get('job_category', 'Unknown')} | "
            f"점수: {result['score']} | "
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
    
    st.subheader(f"📝 {meta['mode']} 스타일 예상 질문")
    
    for i, q in enumerate(result['questions']):
        with st.expander(f"Q{i+1}. {q['q']}", expanded=True):
            st.markdown(f"**🎯 질문 의도:** {q['intent']}")
            st.info(f"**💡 답변 가이드:** {q['tip']}")

    # --- 만족도 조사 UI ---
    st.markdown("---")
    st.markdown("#### 💬 결과가 도움이 되셨나요?")
    st.caption("아래 버튼을 눌러 평가해주시면 서비스 개선에 큰 도움이 됩니다.")
    
    cols = st.columns(5)
    emojis = ["😡", "🙁", "😐", "🙂", "😍"]
    
    def save_feedback(score):
        # [최종 로그] 만족도 포함된 완전한 로그 기록
        full_log = (
            f"[{datetime.datetime.now()}] ⭐ 사용자피드백 | "
            f"만족도: {score}점 | "
            f"직무: {result.get('job_category')} | "
            f"점수: {result['score']} | "
            f"모드: {meta['mode']} | "
            f"JD: {meta['jd_len']}자 | "
            f"Resume: {meta['resume_len']}자"
        )
        print(full_log, flush=True)
        st.toast(f"{score}점 평가 감사합니다! 로그가 저장되었습니다.", icon="✅")
        st.session_state['log_saved'] = True

    # 1~5점 버튼 생성
    for i in range(5):
        if cols[i].button(f"{emojis[i]} {i+1}점", use_container_width=True, key=f"rating_{i}"):
            save_feedback(i+1)
