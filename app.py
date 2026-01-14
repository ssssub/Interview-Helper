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
    # [수정] use_container_width=True 추가 -> 버튼이 컬럼 너비만큼 꽉 차서 중앙 정렬 효과
    analyze_btn = st.button("AI 심층 분석 시작", use_container_width=True)

# 7. AI 분석 로직

# [필수] 세션 스테이트 초기화
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
                # [STEP 1] 점수 채점 + 직무 분류
                print(f"[{datetime.datetime.now()}] 1️⃣ 직무 적합도 및 분류 분석 중... (Gemma-27b)", flush=True)
                
                # Gemma 모델 설정 (JSON 강제 옵션 제외 - 호환성 위해)
                config_strict = {
                    "temperature": 0.0, 
                    "top_p": 1, 
                    "top_k": 1, 
                }
                
                # [수정] 쿼터가 넉넉한 'gemma-3-27b-it' 사용
                model_strict = genai.GenerativeModel('models/gemma-3-27b-it', generation_config=config_strict)
                
                prompt_score = f"""
                You are a strict hiring algorithm.
                
                [Input Data]
                JD: {jd_input}
                Resume: {resume_input}
                
                [Instructions]
                1. Analyze the JD to define 'job_category' (e.g., Backend Dev, Marketing).
                2. Calculate a 'score' (0-100) based strictly on keyword matching between JD and Resume.
                   - Same input must yield the EXACT same score.
                
                [Output Format]
                Provide ONLY a valid JSON object. Do not add markdown blocks like ```json.
                Format:
                {{ "score": 85, "job_category": "Target Job", "summary": "3 line summary", "feedback": "One key improvement" }}
                """
                
                res_score = model_strict.generate_content(prompt_score)
                # 혹시 마크다운이 섞여 나올 경우를 대비한 전처리
                text_score = res_score.text.replace('```json', '').replace('```', '').strip()
                json_score = json.loads(text_score)
                
                
                # [STEP 2] 질문 생성
                print(f"[{datetime.datetime.now()}] 2️⃣ 면접 질문 생성 중...", flush=True)
                
                config_creative = {
                    "temperature": 1.0, 
                }
                # 여기도 Gemma-27b 사용
                model_creative = genai.GenerativeModel('models/gemma-3-27b-it', generation_config=config_creative)
                
                prompt_questions = f"""
                You are a '{mode}' style interviewer.
                Job Category: {json_score['job_category']}
                
                Based on the JD and Resume provided previously, generate 3 sharp interview questions.
                
                [Output Format]
                Provide ONLY a valid JSON object. Do not add markdown blocks.
                {{ "questions": [ {{ "q": "Question text", "intent": "Intent", "tip": "Advice" }}, ... ] }}
                """
                
                res_questions = model_creative.generate_content(prompt_questions)
                text_questions = res_questions.text.replace('```json', '').replace('```', '').strip()
                json_questions = json.loads(text_questions)
                
                
                # [STEP 3] 결과 합치기 및 세션 저장
                final_result = {**json_score, **json_questions}
                
                final_result['meta'] = {
                    'timestamp': str(datetime.datetime.now()),
                    'mode': mode,
                    'jd_len': len(jd_input),
                    'resume_len': len(resume_input)
                }
                
                st.session_state['analysis_result'] = final_result
                st.session_state['log_saved'] = False 
                
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)

            except Exception as e:
                print(f"[{datetime.datetime.now()}] 🚨 오류 발생: {str(e)}", flush=True)
                st.error(f"오류가 발생했습니다: {str(e)}")
                st.stop()

# --- 결과 화면 출력 (기존과 동일) ---
if st.session_state['analysis_result']:
    result = st.session_state['analysis_result']
    meta = result['meta']
    
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

    st.markdown("---")
    st.markdown("#### 💬 결과가 도움이 되셨나요?")
    st.caption("아래 버튼을 눌러 평가해주시면 서비스 개선에 큰 도움이 됩니다.")
    
    cols = st.columns(5)
    emojis = ["😡", "🙁", "😐", "🙂", "😍"]
    
    def save_feedback(score):
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

    for i in range(5):
        if cols[i].button(f"{emojis[i]} {i+1}점", use_container_width=True, key=f"rating_{i}"):
            save_feedback(i+1)
