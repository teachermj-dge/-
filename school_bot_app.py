import streamlit as st
import time
from PIL import Image
import PyPDF2
from google import genai

# 1. 페이지 설정
st.set_page_config(page_title="AI 학교생활기록부 자동화 봇", page_icon="🎓", layout="wide")

# 2. 로그인 로직
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
ALLOWED_EMAILS = ["teacher1@school.ms.kr", "science_teacher@gmail.com", "admin@school.ms.kr"]

if not st.session_state.logged_in:
    st.title("🔒 로그인")
    email = st.text_input("이메일 입력")
    if st.button("로그인"):
        if email in ALLOWED_EMAILS:
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("허가되지 않은 계정입니다.")
    st.stop()

# 3. 메인 화면
st.title("📝 AI 학교생활기록부 특기사항 작성 도우미")

# API Key 설정 (Secrets 사용)
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Secrets에 GEMINI_API_KEY가 설정되지 않았습니다.")
    st.stop()

# 탭 구성 (최대 3명)
tabs = st.tabs([f"학생 {i+1}" for i in range(3)])
students_data = []

for i, tab in enumerate(tabs):
    with tab:
        career = st.text_input("진로 희망", key=f"c_{i}")
        trait = st.text_input("강조 특성", key=f"t_{i}")
        # PDF와 이미지 모두 허용
        uploaded_file = st.file_uploader("보고서/PDF 업로드", type=["jpg", "png", "pdf"], key=f"f_{i}")
        
        file_content = None
        if uploaded_file:
            # 1. PDF 처리 (오류 발생 시 조용히 무시)
            if uploaded_file.type == "application/pdf":
                try:
                    reader = PyPDF2.PdfReader(uploaded_file)
                    text = "".join([p.extract_text() or "" for p in reader.pages])
                    file_content = text
                    st.info("📄 PDF 텍스트 추출 완료")
                except: pass 
            # 2. 이미지 처리 (오류 시 경고만 띄우고 중단하지 않음)
            else:
                try:
                    file_content = Image.open(uploaded_file)
                    st.success("📷 이미지 로드 완료")
                except:
                    st.warning("이미지 형식을 불러올 수 없습니다.")
        
        students_data.append({"id": i+1, "career": career, "trait": trait, "content": file_content})

# 생성 로직 (15초 대기 포함)
if st.button("✨ 전체 생기부 생성"):
    with st.spinner("생성 중입니다..."):
        for s in students_data:
            # 내용에 따른 프롬프트 구성
            content_str = f"보고서 내용: {s['content']}" if isinstance(s['content'], str) else "보고서 데이터 없음"
            prompt = f"진로: {s['career']}, 특성: {s['trait']}. {content_str}. 위 내용을 바탕으로 생기부 문구를 작성하시오."
            
            # API 호출 시도 (3회 재시도)
            for attempt in range(3):
                try:
                    # 이미지인 경우 contents에 이미지 포함, 아닌 경우 텍스트만
                    inputs = [s['content'], prompt] if isinstance(s['content'], Image.Image) else prompt
                    response = client.models.generate_content(model='gemini-2.0-flash', contents=inputs)
                    
                    st.text_area(f"{s['id']}번 학생 결과", value=response.text, height=150)
                    time.sleep(15) # 필수 대기 시간
                    break
                except Exception as e:
                    if attempt < 2:
                        st.warning(f"{s['id']}번 학생 생성 지연... 15초 대기 후 재시도({attempt+1}/3)")
                        time.sleep(15)
                    else:
                        st.error(f"{s['id']}번 학생 생성 실패: {e}")
