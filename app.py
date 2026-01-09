# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import time
import json
import logging

# 1. 로깅 시스템 설정 (Streamlit 서버 로그에 기록됨)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InterviewApp")

# 2. API 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API 키가 설정되지 않았습니다. Streamlit Secrets 설정을 확인해주세요.")

# 3. 디자인 CSS (요청하신 짙은 남색 헤더 및 카드 스타일)
st.set_page_config(page_title="AI 면접 질문 생성기", layout="centered")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .header-container {
        background-color: #1a1f2c;
        padding: 2.5rem;
        border-radius: 0 0 25px 25px;
        color: white;
        text-align: center;
        margin: -6rem -5rem 2rem -5rem;
    }
    .input-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e9ecef;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
        color: white;
        border-radius: 30px;
        padding: 0.7rem 2rem;
        font-weight: bold;
        border: none;
        width: 100%;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }
    .score-box {
        background-color: white;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        border: 2px solid #3b82f6;
        margin-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. 체류 시간 측정 시작
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

# 헤더 섹션
st.markdown("""
    <div class="header-container">
        <h1 style='color: white; margin-bottom: 0;'>💼 AI 면접 질문 생성기</h1>
        <p style='color: #adb5bd;'>채용 공고와 경험을 분석하여 최적의 질문을 제공합니다.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #1a1f2c;'>실전 같은 면접 시뮬레이션</h2>", unsafe_allow_html=True)

# 입력 섹션
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    mode = st.radio("면접관 성향 선택", ["😊 부드러운 면접", "⚡ 압박 면접"], horizontal=True)
    job_desc = st.text_area("채용 공고 (JOB DESCRIPTION)", placeholder="공고 내용을 붙여넣으세요...", height=200)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.write("") # 레이아웃 정렬용
    st.write("") 
    user_exp = st.text_area("나의 경험 / 이력서 (RESUME)", placeholder="자신의 강점을 입력하세요...", height=200)
    st.markdown('</div>', unsafe_allow_html=True)

# 5. 분석 로직 및 로깅
if st.button("✨ 적합도 분석 및 질문 생성"):
    if not job_desc or not user_exp:
        st.warning("내용을 모두 입력해주세요!")
    else:
        with st.spinner("AI 면접관이 데이터를 분석 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                persona = "친절한 사수" if "부드러운" in mode else "깐깐한 면접관"
                
                prompt = f"""
                당신은 {persona}입니다. 다음 정보를 분석하여 반드시 아래 JSON 형식으로만 답변하세요.
                {{
                    "job_category": "개발/마케팅/디자인/영업/기획 중 하나",
                    "fit_score": 0~100 정수,
                    "fit_reason": "한 줄 요약",
                    "questions": [
                        {{"q": "질문", "intent": "의도", "tip": "팁"}}
                    ]
                }}
                [데이터] 공고: {job_desc}, 경험: {user_exp}
                """
                
                response = model.generate_content(prompt)
                data = json.loads(response.text.replace('```json', '').replace('```', '').strip())

                # --- 로깅 시작 (포트폴리오용 핵심 데이터) ---
                end_time = time.time()
                duration = round(end_time - st.session_state.start_time, 2)
                
                # 로그 메시지 생성
                log_data = {
                    "event": "ANALYSIS_COMPLETED",
                    "mode": mode,
                    "job_category": data['job_category'],
                    "fit_score": data['fit_score'],
                    "duration_sec": duration
                }
                logger.info(json.dumps(log_data)) # 시스템 로그에 JSON 형태로 기록
                # ------------------------------------------

                # 결과 화면 출력
                st.markdown(f"""
                    <div class="score-box">
                        <span style='color: #6c757d;'>🎯 직무 적합도 결과</span>
                        <h1 style='color: #2563eb; font-size: 3rem;'>{data['fit_score']}점</h1>
                        <p style='font-weight: bold;'>{data['fit_reason']}</p>
                        <small style='color: #adb5bd;'>분류된 직무군: {data['job_category']}</small>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("### 😈 생성된 면접 질문")
                for i, q in enumerate(data['questions']):
                    with st.expander(f"질문 {i+1}: {q['q']}"):
                        st.write(f"🔍 **면접관 의도:** {q['intent']}")
                        st.write(f"💡 **답변 가이드:** {q['tip']}")

            except Exception as e:
                st.error(f"오류 발생: {e}")
                logger.error(f"ERROR: {str(e)}")

# 6. 하단 만족도 조사 (버튼 클릭 로그 추가)
st.markdown("---")
st.write("생성된 질문이 만족스러우신가요?")
c1, c2 = st.columns(2)
with c1:
    if st.button("👍 만족"):
        logger.info("USER_FEEDBACK: POSITIVE")
        st.success("피드백이 기록되었습니다!")
with c2:
    if st.button("👎 불만족"):
        logger.info("USER_FEEDBACK: NEGATIVE")
        st.info("더 좋은 질문을 위해 개선하겠습니다.")
