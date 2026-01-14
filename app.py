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
if analyze_btn:
    print(f"\n[{datetime.datetime.now()}] 🖱️ '분석 시작' 버튼 클릭됨", flush=True)

    if not jd_input or not resume_input:
        st.warning("⚠️ 정확한 분석을 위해 채용 공고와 이력서 내용을 모두 입력해주세요.")
    else:
        with st.status("🔍 AI 면접관이 서류를 검토하고 있습니다...", expanded=True) as status:
            try:
                # [STEP 1] 점수 채점 (변수 차단 모드)
                print(f"[{datetime.datetime.now()}] 1️⃣ 직무 적합도 정밀 채점 중...", flush=True)
                
                # [핵심 설정 1] top_k를 1로 설정하여 '무조건 1등 답변'만 선택하게 강제
                config_strict = {
                    "temperature": 0.0, 
                    "top_p": 1,
                    "top_k": 1, # <--- 여기가 핵심! (변수 창출 원천 봉쇄)
                    "response_mime_type": "application/json",
                }
                
                # 요청하신 모델명 적용
                model_strict = genai.GenerativeModel('models/gemini-2.5-flash', generation_config=config_strict)
                
                # [핵심 설정 2] '느낌'이 아니라 '계산'을 하도록 알고리즘 지시
                prompt_score = f"""
                당신은 엄격한 채점 알고리즘입니다. 
                아래 [채점 기준]에 따라 기계적으로 점수를 계산하세요. 추론하지 말고 계산하세요.

                [입력 데이터] 
                JD: {jd_input}
                이력서: {resume_input}
                
                [채점 기준 Algorithm]
                1. JD에 명시된 '핵심 역량/기술' 키워드를 추출하세요.
                2. 이력서에 해당 키워드가 있는지 1:1로 대조하세요.
                3. (매칭된 키워드 수 / 전체 핵심 키워드 수) * 100 으로 점수를 산출하세요.
                4. 결과값은 소수점을 버리고 정수로 출력하세요.
                
                **중요: 동일한 입력값에 대해서는 반드시 비트 단위로 동일한 점수가 나와야 합니다.**

                JSON 형식: {{ "score": 숫자, "summary": "3줄 요약", "feedback": "핵심 보완점 1개" }}
                """
                
                res_score = model_strict.generate_content(prompt_score)
                json_score = json.loads(res_score.text)
                
                
                # [STEP 2] 질문 생성 (다양성 모드)
                print(f"[{datetime.datetime.now()}] 2️⃣ 면접 질문 생성 중...", flush=True)
                
                # 질문은 매번 달라야 하므로 temperature 1.0 유지
                config_creative = {
                    "temperature": 1.0, 
                    "response_mime_type": "application/json",
                }
                model_creative = genai.GenerativeModel('models/gemini-2.5-flash', generation_config=config_creative)
                
                prompt_questions = f"""
                당신은 '{mode}' 스타일의 면접관입니다.
                
                지원자 정보(JD, 이력서)를 바탕으로 면접 질문 3가지를 생성하세요.
                이전과 다른 창의적이고 날카로운 질문을 던지세요.
                
                JSON 형식: {{ "questions": [ {{ "q": "질문", "intent": "의도", "tip": "팁" }}, ... ] }}
                """
                
                res_questions = model_creative.generate_content(prompt_questions)
                json_questions = json.loads(res_questions.text)
                
                
                # [STEP 3] 결과 합치기
                final_result = {**json_score, **json_questions}
                
                # 로그 확인
                score = final_result.get('score', 0)
                q_count = len(final_result.get('questions', []))
                print(f"[{datetime.datetime.now()}] ✅ 최종 완료 | 점수: {score}점 (고정됨) | 질문: {q_count}개", flush=True)
                
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                
                # --- 화면 출력 ---
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="result-card" style="text-align: center;">
                    <span class="score-badge">직무 적합도</span>
                    <h1 style="color: #1E293B; font-size: 3.5rem; margin: 10px 0;">{final_result['score']}<span style="font-size: 1.5rem; color: #94A3B8;">/100</span></h1>
                    <p style="font-size: 1.1rem; color: #475569;">{final_result['summary']}</p>
                    <div style="background: #F1F5F9; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: left;">
                        <strong style="color: #334155;">💡 보완 Tip:</strong> <span style="color: #475569;">{final_result['feedback']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.subheader(f"📝 {mode} 스타일 예상 질문")
                
                for i, q in enumerate(final_result['questions']):
                    with st.expander(f"Q{i+1}. {q['q']}", expanded=True):
                        st.markdown(f"**🎯 질문 의도:** {q['intent']}")
                        st.info(f"**💡 답변 가이드:** {q['tip']}")

            except Exception as e:
                print(f"[{datetime.datetime.now()}] 🚨 오류 발생: {str(e)}", flush=True)
                st.error(f"오류가 발생했습니다: {str(e)}")
