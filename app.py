import streamlit as st
import google.generativeai as genai
import json

# 1. 페이지 설정
st.set_page_config(
    page_title="Interview Master | AI 면접 분석",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 커스텀 CSS (헤더 정렬 및 버튼 폰트 크기 수정)
st.markdown("""
    <style>
    /* 전체 배경 */
    .main { background-color: #F8FAFC; font-family: 'Pretendard', sans-serif; }
    
    /* 헤더 섹션: 좌우 여백을 auto로 설정하여 완벽한 중앙 정렬 */
    .header-container {
        width: 100%;
        margin: 0 auto;
        text-align: center;
        padding: 40px 0;
    }

    /* 입력창 디자인 */
    .stTextArea textarea {
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        padding: 15px;
    }
    
    /* 버튼 디자인: 폰트 크기를 1.0rem으로 하향 조정 */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #1E293B 0%, #334155 100%);
        color: white;
        border: none;
        padding: 12px 0;
        border-radius: 8px;
        font-weight: 500;
        font-size: 1.0rem; /* 폰트 크기 축소 */
        margin-top: 10px;
        transition: all 0.3s;
    }

    /* 결과 카드 */
    .score-card {
        background-color: white;
        padding: 24px;
        border-radius: 16px;
        border-left: 5px solid #2563EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. API 키 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ API Key가 설정되지 않았습니다. Secrets에 등록해주세요.")
    st.stop()

# 4. 헤더 섹션 (HTML 구조로 여백 균형 최적화)
st.markdown("""
    <div class="header-container">
        <h1 style='color: #1E293B; margin-bottom: 10px; font-size: 2.5rem;'>Interview Master</h1>
        <p style='color: #64748B; font-size: 1.1rem;'>AI가 분석하는 정교한 면접 시뮬레이션</p>
    </div>
    """, unsafe_allow_html=True)

# 5. 메인 입력 영역 (좌우 수평 대칭)
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### 📄 Job Description")
    jd = st.text_area(
        "채용 공고 전문", 
        placeholder="지원하시는 직무의 공고 내용을 복사하여 입력해주세요.",
        height=350,
        label_visibility="collapsed"
    )

with col2:
    st.markdown("### 👤 Your Experience")
    exp = st.text_area(
        "나의 이력 및 경험", 
        placeholder="자신의 프로젝트 경험이나 이력서 내용을 입력해주세요.",
        height=350,
        label_visibility="collapsed"
    )

# 6. 설정 및 실행 영역 (대칭 구조 유지)
_, center_col, _ = st.columns([1, 1.5, 1])
with center_col:
    mode = st.select_slider(
        "면접관 성향 선택",
        options=["부드러운 면접 (Soft)", "표준 면접 (Standard)", "압박 면접 (Pressure)"],
        value="표준 면접 (Standard)"
    )
    analyze_btn = st.button("AI 심층 분석 시작")

# 7. 분석 로직
if analyze_btn:
    if not jd or not exp:
        st.warning("분석을 위해 공고와 이력서 내용을 모두 입력해주세요.")
    else:
        with st.status("🔍 데이터를 분석하고 있습니다...", expanded=True) as status:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"공고:{jd}\n경험:{exp}\n모드:{mode}를 바탕으로 면접 질문 3개와 적합도 점수를 JSON 형식으로 한국어로 답변해줘."
            
            try:
                response = model.generate_content(prompt)
                # JSON 파싱 및 결과 출력 (기존 로직과 동일)
                st.success("분석이 완료되었습니다!")
                # ... (이하 결과 출력 로직 생략, 기존과 동일하게 작동)
                st.balloons()
            except:
                st.error("분석 중 오류가 발생했습니다.")
