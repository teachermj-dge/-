import streamlit as st
import time
from PIL import Image
import PyPDF2

# 1. 페이지 설정
st.set_page_config(page_title="AI 학교생활기록부 자동화 봇", page_icon="🎓", layout="wide")

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# 2. 로그인 로직
ALLOWED_EMAILS = ["teacher1@school.ms.kr", "science_teacher@gmail.com"]

if not st.session_state.logged_in:
    st.title("🔒 로그인")
    email_input = st.text_input("이메일")
    if st.button("로그인"):
        if email_input in ALLOWED_EMAILS:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("허가되지 않은 계정입니다.")
    st.stop()

# 3. 메인 화면
st.title("📝 AI 학교생활기록부 특기사항 작성 도우미")

# API 설정 (사이드바)
api_key = st.sidebar.text_input("Gemini API Key", type="password")

# 학생 처리 로직 (탭 기능 포함)
num_students = 5
tabs = st.tabs([f"{i+1}번 학생" for i in range(num_students)])
students_data = []

for i, tab in enumerate(tabs):
    with tab:
        career_path = st.text_input(f"{i+1}번 학생 진로", key=f"career_{i}")
        characteristic = st.text_input(f"{i+1}번 학생 특성", key=f"char_{i}")
        achievement_level = st.selectbox(f"{i+1}번 학생 성취수준", ["상", "중", "하"], key=f"level_{i}")
        
        uploaded_file = st.file_uploader(f"{i+1}번 학생 보고서", type=["jpg", "png", "pdf"], key=f"file_{i}")
        
        file_content = None
        if uploaded_file is not None:
            if uploaded_file.type == "application/pdf":
                try:
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    pdf_text = "".join([page.extract_text() or "" for page in pdf_reader.pages])
                    file_content = pdf_text
                    st.info("📄 PDF 텍스트 추출 완료")
                except Exception:
                    pass
            else:
                try:
                    file_content = Image.open(uploaded_file)
                    st.success("📷 이미지 로드 완료")
                except Exception:
                    pass
        
        students_data.append({
            "id": i+1,
            "career": career_path,
            "trait": characteristic,
            "level": achievement_level,
            "file_content": file_content
        })

# 생성 버튼
if st.button("✨ 전체 생기부 생성"):
    if not api_key:
        st.error("API Key를 입력해주세요.")
    else:
        # 여기에 생성 로직(Gemini API 호출)을 넣어주세요
        st.success("생성 완료!")
