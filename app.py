# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import time
import json
import logging

# 1. 로깅 설정 (포트폴리오용 데이터 수집)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InterviewApp")

# 2. API 설정 및 보안
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets 설정을 확인해주세요.")

# 3. 페이지 설정 및 디자인 (차분한 면접장 테마)
st.set_page_config(page_title="1분 역전: 면접 압박 질문기", page_icon="⚖️", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #1e293b; color: white; }
    .score-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; text-align: center; margin-bottom: 20px; }
    .question-card { background-color: #f1f5f9; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# 4. 체류 시간 측정을 위한 세션 상태 초기화
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

# 헤더
st.title("⚖️ 1분 역전: 면접 질문기")
st.write("채용 공고와 당신의 경험을 분석하여 최적의 면접 대비 전략을 드립니다.")

# 5. 입력 세션
with st.container():
    mode = st.radio("면접 모드 선택", ["부드러운 면접", "압박 면접"], horizontal=True)
    job_desc = st.text_area("채용 공고 내용", placeholder="채용 공고의 주요 직무와 우대 사항을 입력하세요.", height=150)
    user_exp = st.text_area("자신의 경험/이력서 요약", placeholder="주요 프로젝트 성과나 보유 역량을 입력하세요.", height=150)

# 6. 메인 로직 (생성하기 버튼 클릭 시)
if st.button("분석 및 질문 생성 시작"):
    if not job_desc or not user_exp:
        st.warning("내용을 모두 입력해 주세요.")
    else:
        with st.spinner("AI 면접관이 데이터를 심층 분석 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 프롬프트 구성 (React 앱에서 구현한 로직 그대로 이식)
                persona = "부드럽고 친절한 사수" if mode == "부드러운 면접" else "매우 날카롭고 압박을 가하는 면접관"
                
                prompt = f"""
                당신은 {persona}입니다. 다음 정보를 바탕으로 분석 결과를 JSON 형식으로만 답변하세요.
                1. 직무 카테고리(job_category): 개발, 디자인, 마케팅, 기획, 영업 중 하나로 분류
                2. 직무 적합도(fit_score): 0~100점 사이 정수
                3. 적합도 이유(fit_reason): 한 줄 평
                4. 질문 리스트(questions): 질문 내용, 면접관의 의도, 답변 팁을 포함한 3개의 질문

                [채용 공고]: {job_desc}
                [지원자 경험]: {user_exp}
                
                JSON 형식 예시:
                {{
                    "job_category": "분류된 직무",
                    "fit_score": 85,
                    "fit_reason": "공고의 역량과 실제 경험이 유사함",
                    "questions": [
                        {{"q": "질문1", "intent": "의도1", "tip": "팁1"}},
                        ...
                    ]
                }}
                """
                
                response = model.generate_content(prompt)
                # JSON 문자열만 추출 (코드 블록 제거)
                json_str = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(json_str)

                # 체류 시간 계산
                duration = round(time.time() - st.session_state.start_time, 2)
                
                # 로그 남기기 (나중에 이 내용을 긁어서 포트폴리오 데이터로 활용)
                logger.info(f"JOB_CAT: {data['job_category']}, SCORE: {data['fit_score']}, DURATION: {duration}s")

                # 7. 결과 화면 렌더링
                st.markdown("---")
                
                # 적합도 점수 카드
                st.markdown(f"""
                <div class="score-card">
                    <h4>🎯 직무 적합도 점수</h4>
                    <h1 style="color: #1e293b;">{data['fit_score']}점</h1>
                    <p>{data['fit_reason']}</p>
                    <small>분류된 직무: {data['job_category']}</small>
                </div>
                """, unsafe_allow_html=True)

                # 질문 리스트
                st.subheader(f"😈 {mode} 모드 질문")
                for i, q in enumerate(data['questions']):
                    with st.expander(f"질문 {i+1}: {q['q']}"):
                        st.info(f"💡 **면접관의 의도:** {q['intent']}")
                        st.success(f"✅ **답변 팁:** {q['tip']}")

                # 만족도 체크
                st.markdown("---")
                st.write("이 질문들이 실제 면접 대비에 도움이 되나요?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 도움이 됨"):
                        logger.info("FEEDBACK: POSITIVE")
                        st.toast("피드백이 반영되었습니다!")
                with col2:
                    if st.button("👎 아쉬움"):
                        logger.info("FEEDBACK: NEGATIVE")
                        st.toast("더 정교한 질문을 만들도록 노력할게요.")

            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")

# 하단 정보
st.caption(f"앱 사용 시간: {round(time.time() - st.session_state.start_time, 1)}초")
