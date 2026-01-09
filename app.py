import streamlit as st
import google.generativeai as genai
import json

# 1. 페이지 설정: 제목과 아이콘, 레이아웃 최적화
st.set_page_config(
    page_title="Interview Master | AI 면접 분석",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 전문적인 커스텀 CSS (대칭 및 여백 최적화)
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 설정 */
    .main { background-color: #F8FAFC; font-family: 'Pretendard', sans-serif; }
    
    /* 카드형 컨테이너 디자인 */
    .stTextArea textarea {
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        padding: 15px;
        line-height: 1.6;
    }
    
    /* 수평 정렬을 위한 버튼 디자인 */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #1E293B 0%, #334155 100%);
        color: white;
        border: none;
        padding: 12px 0;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1.1rem;
        margin-top: 20px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* 점수 카드 디자인 */
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

# 3. API 키 설정 (보안)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ API Key가 설정되지 않았습니다. Secrets에 등록해주세요.")
    st.stop()

# 4. 헤더 섹션 (중앙 정렬 및 대칭)
st.markdown("<h1 style='text-align: center; color: #1E293B; margin-bottom: 0;'>Interview Master</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B; font-size: 1.1rem; margin-bottom: 40px;'>AI가 분석하는 정교한 면접 시뮬레이션</p>", unsafe_allow_html=True)

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

# 6. 설정 및 실행 영역 (중앙 정렬 강조)
_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    mode = st.select_slider(
        "면접관 성향 선택",
        options=["부드러운 면접 (Soft)", "표준 면접 (Standard)", "압박 면접 (Pressure)"],
        value="표준 면접 (Standard)"
    )
    analyze_btn = st.button("AI 심층 분석 시작")

# 7. 분석 로직 및 결과 출력
if analyze_btn:
    if not jd or not exp:
        st.warning("분석을 위해 공고와 이력서 내용을 모두 입력해주세요.")
    else:
        with st.status("🔍 데이터를 분석하고 있습니다...", expanded=True) as status:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            너는 대기업 인사팀의 베테랑 면접관이야. 공고와 경험을 비교해줘.
            [공고]: {jd}
            [경험]: {exp}
            [모드]: {mode}
            
            다음 JSON 형식으로만 엄격하게 답변해:
            {{
                "fitScore": 0~100 숫자,
                "fitReason": "적합도 요약 (존댓말)",
                "questions": [
                    {{"q": "질문", "intent": "의도", "tip": "조언"}}
                ]
            }}
            한국어로 답변할 것.
            """
            
            try:
                response = model.generate_content(prompt)
                json_data = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)

                # 결과 섹션 (수평 정렬 강조)
                st.markdown("---")
                
                # 상단 점수 카드
                st.markdown(f"""
                    <div class="score-card">
                        <h2 style='margin-top:0; color:#1E293B;'>🎯 직무 적합도 점수: {json_data['fitScore']}점</h2>
                        <p style='color:#475569; line-height:1.6; font-size:1.05rem;'>{json_data['fitReason']}</p>
                    </div>
                """, unsafe_allow_html=True)

                # 하단 질문 리스트 (대칭 구조)
                st.markdown("### 💡 예상 면접 질문")
                for i, q in enumerate(json_data['questions']):
                    with st.expander(f"Q{i+1}. {q['q']}"):
                        st.markdown(f"**🎯 출제 의도**\n\n{q['intent']}")
                        st.success(f"**💡 답변 가이드**\n\n{q['tip']}")
                
                st.balloons()

            except Exception as e:
                st.error("데이터 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
