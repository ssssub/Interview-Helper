import streamlit as st
import google.generativeai as genai
import json

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
    if not jd_input or not resume_input:
        st.warning("⚠️ 정확한 분석을 위해 채용 공고와 이력서 내용을 모두 입력해주세요.")
    else:
        with st.status("🔍 AI 면접관이 서류를 검토하고 있습니다...", expanded=True) as status:
            try:
                # [중요 변경 1] 일관성을 위해 temperature를 0으로 설정 (점수가 흔들리지 않게 함)
                generation_config = {
                    "temperature": 0.0,
                    "top_p": 1,
                    "top_k": 32,
                    "max_output_tokens": 4096,
                }
                
                model = genai.GenerativeModel('models/gemini-2.5-flash', generation_config=generation_config)
                
                # [중요 변경 2] 프롬프트에서 점수 평가와 질문 생성을 명확히 분리
                prompt = f"""
                당신은 전문 채용 담당자입니다. 아래 두 가지 작업을 순서대로 수행하세요.

                [입력 데이터]
                1. 채용 공고: {jd_input}
                2. 지원자 정보: {resume_input}
                3. 면접 모드: {mode}

                [작업 지시사항]
                STEP 1. 직무 적합도 평가 (Objective Scoring):
                - '면접 모드'와 관계없이, 오직 채용 공고와 지원자 정보의 일치도만을 기준으로 객관적으로 평가하세요.
                - 압박 면접이라고 해서 점수를 낮게 주거나, 부드러운 면접이라고 해서 점수를 높게 주면 안 됩니다.
                - 0~100점 사이의 점수를 냉정하게 산출하세요.

                STEP 2. 면접 질문 생성 (Roleplay):
                - 이제 '{mode}'의 페르소나를 적용하여 질문을 생성하세요.
                - 질문의 어조와 강도는 '{mode}'를 철저히 따르세요.

                [출력 형식]
                반드시 아래 JSON 형식으로만 출력하세요 (Markdown 코드 블록 제외):
                {{
                    "score": 0~100 숫자,
                    "summary": "적합도 평가 요약 (정중한 말투)",
                    "feedback": "보완점 한 가지",
                    "questions": [
                        {{
                            "q": "질문 내용",
                            "intent": "의도",
                            "tip": "답변 팁"
                        }},
                        {{
                            "q": "질문 내용",
                            "intent": "의도",
                            "tip": "답변 팁"
                        }},
                        {{
                            "q": "질문 내용",
                            "intent": "의도",
                            "tip": "답변 팁"
                        }}
                    ]
                }}
                """
                
                response = model.generate_content(prompt)
                
                try:
                    text_response = response.text.replace('```json', '').replace('```', '').strip()
                    result = json.loads(text_response)
                except json.JSONDecodeError:
                    st.error("AI 응답 처리 중 오류가 발생했습니다. 다시 시도해주세요.")
                    st.stop()
                
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 결과 출력
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
                st.error(f"오류가 발생했습니다: {str(e)}")
