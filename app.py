import streamlit as st
import google.generativeai as genai
import json

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="1분 역전: 면접 압박 질문 생성기", page_icon="⚡", layout="wide")

# CSS 스타일 적용 (오타 수정됨: unsafe_allow_html=True)
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 50px; height: 3em; background-color: #2563eb; color: white; font-weight: bold; }
    .stTextArea>div>div>textarea { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. API 키 설정 (Secrets 활용)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API 키가 설정되지 않았습니다. Streamlit Settings > Secrets에 키를 등록해주세요.")
    st.stop()

# 3. 화면 구성
st.title("⚡ 1분 역전: 실전 면접 시뮬레이션")
st.caption("면접관의 성향을 선택하고 공고와 이력서를 입력하세요. AI가 당신의 약점을 분석합니다.")

# 4. 입력 섹션
col1, col2 = st.columns(2)

with col1:
    jd = st.text_area("📄 채용 공고 (Job Description)", placeholder="주요 업무 및 자격 요건을 입력하세요...", height=300)

with col2:
    exp = st.text_area("👤 나의 경험 / 이력서 (Resume)", placeholder="프로젝트 경험이나 자기소개서 내용을 입력하세요...", height=300)

mode = st.radio("😈 면접관 성향 선택", ["부드러운 면접 (Soft)", "압박 면접 (Pressure)"], horizontal=True)

# 5. 분석 로직
if st.button("적합도 분석 및 질문 생성"):
    if not jd or not exp:
        st.warning("내용을 모두 입력해주세요!")
    else:
        with st.spinner("AI 면접관이 서류를 검토 중입니다..."):
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            너는 전문 면접관이야. 아래 채용 공고와 지원자의 경험을 바탕으로 면접 질문을 생성해줘.
            
            [채용 공고]: {jd}
            [지원자 경험]: {exp}
            [면접 모드]: {mode}
            
            다음 형식의 JSON으로만 응답해줘:
            {{
                "fitScore": 0~100 사이의 점수,
                "fitReason": "적합도 점수에 대한 요약 이유",
                "jobCategory": "직무 카테고리",
                "questions": [
                    {{
                        "question": "면접 질문 내용",
                        "intent": "질문의 의도",
                        "tip": "답변 가이드라인"
                    }}
                ]
            }}
            압박 면접 모드일 경우 훨씬 날카롭고 꼬리를 무는 질문을 만들어줘. 모든 답변은 한국어로 해줘.
            """
            
            try:
                response = model.generate_content(prompt)
                json_str = response.text.replace('```json', '').replace('```', '').strip()
                result = json.loads(json_str)
                
                # 6. 결과 화면
                st.divider()
                st.subheader(f"🎯 직무 적합도 점수: {result['fitScore']}점")
                st.info(result['fitReason'])
                
                st.markdown(f"### {'😈 생성된 압박 질문' if 'Pressure' in mode else '😊 생성된 면접 질문'}")
                
                for i, q in enumerate(result['questions']):
                    with st.expander(f"질문 {i+1}: {q['question']}"):
                        st.write(f"**💡 질문 의도:** {q['intent']}")
                        st.success(f"**📝 답변 팁:** {q['tip']}")
                        
                st.balloons()
                
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다. 입력을 확인하거나 잠시 후 다시 시도해 주세요.")
