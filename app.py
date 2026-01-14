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
    # [로그] 버튼 클릭 즉시 기록
    print(f"\n[{datetime.datetime.now()}] 🖱️ '분석 시작' 버튼 클릭됨", flush=True)

    if not jd_input or not resume_input:
        st.warning("⚠️ 정확한 분석을 위해 채용 공고와 이력서 내용을 모두 입력해주세요.")
        # [로그] 입력 누락 기록
        print(f"[{datetime.datetime.now()}] ⚠️ 입력 데이터 누락", flush=True)
    else:
        with st.status("🔍 AI 면접관이 서류를 검토하고 있습니다...", expanded=True) as status:
            try:
                # [로그] 분석 시작 기록
                print(f"[{datetime.datetime.now()}] ▶️ AI 분석 시작 | 모드: {mode} | JD: {len(jd_input)}자 | 이력서: {len(resume_input)}자", flush=True)

                # [핵심 설정 1] temperature: 0.0 -> 점수가 절대 흔들리지 않게 고정 (일관성 100%)
                generation_config = {
                    "temperature": 0.0, 
                    "top_p": 1,
                    "top_k": 32,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                }
                
                # [모델명] 요청하신 'models/gemini-2.5-flash' 적용
                model = genai.GenerativeModel('models/gemini-2.5-flash', generation_config=generation_config)
                
                # [프롬프트] '기계적/정량적 채점'을 강력하게 지시
                prompt = f"""
                당신은 감정이 없는 냉철한 AI 채용 평가 알고리즘입니다.

                [입력 데이터]
                1. 채용 공고(JD): {jd_input}
                2. 지원자 정보: {resume_input}
                3. 면접 모드: {mode}

                [작업 지시사항]
                STEP 1. 직무 적합도 점수 산출 (Strict Quantitative Scoring):
                - 점수는 오직 'JD의 필수 역량 키워드'가 '지원자 이력서'에 존재하는지 여부를 기계적으로 계산하여 산출하세요.
                - 인간적인 직관이나 느낌을 배제하고, 키워드 매칭률(%)을 그대로 점수(0~100)로 환산하세요.
                - 따라서 동일한 JD와 이력서가 입력되면, 언제나 100% 동일한 점수가 출력되어야 합니다.

                STEP 2. 면접 질문 생성:
                - '{mode}'의 페르소나를 적용하여 질문을 생성하세요.

                [출력 형식]
                반드시 JSON 형식으로만 응답하세요.
                {{
                    "score": 0~100 숫자 (매칭률 기반 정수),
                    "summary": "적합도 평가 요약 (정중한 말투)",
                    "feedback": "보완점 한 가지",
                    "questions": [
                        {{ "q": "질문", "intent": "의도", "tip": "팁" }},
                        {{ "q": "질문", "intent": "의도", "tip": "팁" }},
                        {{ "q": "질문", "intent": "의도", "tip": "팁" }}
                    ]
                }}
                """
                
                # API 호출
                response = model.generate_content(prompt)
                
                # 결과 처리
                try:
                    # JSON 모드 사용 시 바로 파싱 가능
                    result = json.loads(response.text)
                    
                    # [로그] 성공 기록 (점수 확인용)
                    score = result.get('score', 0)
                    q_count = len(result.get('questions', []))
                    print(f"[{datetime.datetime.now()}] ✅ 분석 성공! | 점수: {score}점 | 질문수: {q_count}개", flush=True)

                except Exception as e:
                    # [로그] 실패 시 원본 확인
                    print(f"[{datetime.datetime.now()}] ❌ 파싱 오류: {str(e)}", flush=True)
                    st.error("AI 응답 처리 중 오류가 발생했습니다.")
                    st.stop()
                
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                
                # 결과 화면 출력
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="result-card" style="text-align: center;">
                    <span class="score-badge">직무 적합도</span>
                    <h1 style="color: #1E293B; font-size: 3.5rem; margin: 10px 0;">{result['score']}<span style="font-size: 1.5rem; color: #94A3B8;">/100</span></h1>
                    <p style="font-size: 1.1rem; color: #475569;">{result['summary']}</p>
                    <div style="background: #F1F5F9; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: left;">
                        <strong style="color: #334155;">💡 보완 Tip:</strong> <span style="color: #475569;">{result['feedback']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.subheader(f"📝 {mode} 스타일 예상 질문")
                
                for i, q in enumerate(result['questions']):
                    with st.expander(f"Q{i+1}. {q['q']}", expanded=True):
                        st.markdown(f"**🎯 질문 의도:** {q['intent']}")
                        st.info(f"**💡 답변 가이드:** {q['tip']}")
                        
            except Exception as e:
                # [로그] 시스템 에러
                print(f"[{datetime.datetime.now()}] 🚨 시스템 오류: {str(e)}", flush=True)
                st.error(f"오류가 발생했습니다: {str(e)}")
