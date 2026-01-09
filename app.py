import streamlit as st
import google.generativeai as genai
import json

# 1. 페이지 기본 설정 (넓은 레이아웃, 아이콘)
st.set_page_config(
    page_title="Interview Master | AI 면접 분석",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 전문적인 디자인을 위한 커스텀 CSS 적용
st.markdown("""
    <style>
    /* 폰트 및 기본 배경 설정 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif; 
    }
    
    .main {
        background-color: #F8FAFC; 
    }
    
    /* 헤더 컨테이너: 완벽한 중앙 정렬 및 여백 */
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

    /* 입력창(TextArea) 스타일링 */
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
    
    /* 섹션 제목 스타일 */
    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* 버튼 스타일링 (요청사항 반영: 폰트 크기 축소, 정중앙) */
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
        font-size: 1.0rem; /* 요청하신 폰트 크기 */
        letter-spacing: 0.02rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    /* 결과 카드 스타일 */
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

# 3. API 키 설정 (보안)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ API Key 오류: Streamlit Secrets에 GEMINI_API_KEY를 등록해주세요.")
    st.stop()

# 4. 메인 헤더 (중앙 정렬)
st.markdown("""
    <div class="header-container">
        <div class="header-title">Interview Master</div>
        <div class="header-subtitle">AI 기반 면접관이 당신의 이력서와 공고를 분석하여 질문을 생성합니다</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 5. 입력 섹션 (좌우 대칭 구조)
# st.columns의 gap="large"를 통해 시원한 여백 확보
left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.markdown('<div class="section-header">📄 채용 공고 (JD)</div>', unsafe_allow_html=True)
    jd_input = st.text_area(
        "jd_input",
        placeholder="지원하려는 공고의 주요 업무 및 자격 요건을 복사해 붙여넣으세요.",
        height=400,
        label_visibility="collapsed"
    )

with right_col:
    st.markdown('<div class="section-header">👤 나의 이력서 / 경험</div>', unsafe_allow_html=True)
    resume_input = st.text_area(
        "resume_input",
        placeholder="자신의 이력서, 자기소개서, 또는 주요 프로젝트 경험을 입력하세요.",
        height=400,
        label_visibility="collapsed"
    )

# 6. 컨트롤 섹션 (슬라이더 및 버튼 중앙 배치)
st.markdown("<br>", unsafe_allow_html=True)
_, center_col, _ = st.columns([1, 2, 1]) # 1:2:1 비율로 중앙 집중

with center_col:
    mode = st.select_slider(
        "면접관 스타일을 선택하세요",
        options=["부드러운 면접 (Soft)", "표준 면접 (Standard)", "압박 면접 (Pressure)"],
        value="표준 면접 (Standard)"
    )
    
    analyze_btn = st.button("AI 심층 분석 시작")

# 7. AI 분석 로직 및 결과 표시
if analyze_btn:
    if not jd_input or not resume_input:
        st.warning("⚠️ 정확한 분석을 위해 채용 공고와 이력서 내용을 모두 입력해주세요.")
    else:
        with st.status("🔍 AI 면접관이 서류를 검토하고 있습니다...", expanded=True) as status:
            try:
                # 프롬프트 엔지니어링
                model = genai.GenerativeModel('gemini-pro')
                prompt = f"""
                당신은 10년 차 채용 담당 면접관입니다. 다음 정보를 바탕으로 분석을 수행하세요.
                
                [채용 공고]: {jd_input}
                [지원자 정보]: {resume_input}
                [면접 모드]: {mode}
                
                아래 JSON 형식으로만 응답하세요 (Markdown 코드 블록 없이 순수 JSON만 출력):
                {{
                    "score": 0~100 사이의 숫자,
                    "summary": "지원자의 적합도에 대한 한 줄 총평 (정중한 말투)",
                    "feedback": "이력서에서 보완하면 좋을 점 한 가지",
                    "questions": [
                        {{
                            "q": "면접 질문 내용",
                            "intent": "질문 의도",
                            "tip": "답변 가이드"
                        }},
                        {{
                            "q": "면접 질문 내용",
                            "intent": "질문 의도",
                            "tip": "답변 가이드"
                        }},
                        {{
                            "q": "면접 질문 내용",
                            "intent": "질문 의도",
                            "tip": "답변 가이드"
                        }}
                    ]
                }}
                모드는 '{mode}'를 철저히 반영하여 질문의 톤앤매너를 결정하세요.
                """
                
                response = model.generate_content(prompt)
                
                # JSON 파싱 (오류 방지 처리)
                try:
                    text_response = response.text.replace('```json', '').replace('```', '').strip()
                    result = json.loads(text_response)
                except json.JSONDecodeError:
                    st.error("AI 응답을 처리하는 중 오류가 발생했습니다. 다시 시도해주세요.")
                    st.stop()
                
                status.update(label="✅ 분석 완료! 결과를 확인하세요.", state="complete", expanded=False)
                
                # 결과 화면 출력
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 종합 점수 카드
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
                
                # 질문 리스트
                st.subheader("📝 예상 면접 질문")
                
                for i, q in enumerate(result['questions']):
                    with st.expander(f"Q{i+1}. {q['q']}", expanded=True):
                        st.markdown(f"**🎯 질문 의도:** {q['intent']}")
                        st.info(f"**💡 답변 가이드:** {q['tip']}")
                        
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
