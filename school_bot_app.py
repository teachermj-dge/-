import streamlit as st
import time
from PIL import Image
import PyPDF2
from google import genai

# 1. 페이지 설정
st.set_page_config(page_title="AI 학교생활기록부 자동화 봇", page_icon="🎓", layout="wide")

# 세션 상태 초기화
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_email' not in st.session_state: st.session_state.user_email = ""

# 2. 사용자 인증
ALLOWED_EMAILS = ["teacher1@school.ms.kr", "science_teacher@gmail.com", "admin@school.ms.kr"]

def simulate_login(email):
    if email in ALLOWED_EMAILS:
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.rerun()
    elif email == "": st.warning("이메일을 입력해주세요.")
    else: st.error("허가되지 않은 계정입니다.")

if not st.session_state.logged_in:
    st.title("🔒 학교 전용 특기사항 자동화 봇")
    with st.form("login_form"):
        email_input = st.text_input("이메일 주소 입력")
        if st.form_submit_button("인증 및 로그인"): simulate_login(email_input)
    st.stop()

# 3. 메인 화면
col_title, col_user = st.columns([8, 2])
with col_title: st.title("📝 AI 학교생활기록부 특기사항 작성 도우미")
with col_user: 
    st.write(f"👤 {st.session_state.user_email}")
    if st.button("로그아웃"): 
        st.session_state.logged_in = False
        st.rerun()

st.sidebar.title("⚙️ API 설정")
api_key_input = st.sidebar.text_input("Gemini API Key", type="password")
client = genai.Client(api_key=api_key_input) if api_key_input else None

# 4. 설정 및 데이터 입력
record_types = ["자율 활동 특기 사항", "동아리 활동 특기 사항", "진로 활동 특기 사항", "과목 별 세부 능력 및 특기 사항", "행동특성 및 종합의견"]
selected_record_type = st.radio("작성할 영역:", record_types, horizontal=True)

activity_name = st.text_input("활동명 (필수)")
num_students = st.selectbox("입력할 학생 수", [1, 2, 3, 4, 5])
tabs = st.tabs([f"학생 {i+1}" for i in range(num_students)])
students_data = []

for i, tab in enumerate(tabs):
    with tab:
        col1, col2 = st.columns(2)
        with col1:
            career = st.text_input("진로 희망", key=f"c_{i}")
            trait = st.text_input("강조 특성", key=f"t_{i}")
        with col2:
            level = st.selectbox("성취수준", ["선택 안 함", "상", "중", "하"], key=f"l_{i}")
            uploaded_file = st.file_uploader(f"보고서/PDF 업로드", type=["jpg", "png", "pdf"], key=f"f_{i}")
        
        file_data = None
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                try:
                    reader = PyPDF2.PdfReader(uploaded_file)
                    file_data = "".join([p.extract_text() or "" for p in reader.pages])
                    st.info("📄 PDF 텍스트 추출 완료")
                except: pass # 오류시 조용히 무시
            else:
                try:
                    file_data = Image.open(uploaded_file)
                    st.success("📷 이미지 로드 완료")
                except: st.warning("이미지 형식을 불러올 수 없습니다.")
        
        students_data.append({"id": i+1, "career": career, "trait": trait, "level": level, "data": file_data})

# 5. 생성 로직
if st.button("✨ 전체 생기부 생성", type="primary"):
    if not client: st.error("API Key를 입력해주세요.")
    else:
        for s in students_data:
            prompt = f"진로: {s['career']}, 특성: {s['trait']}, 성취수준: {s['level']}. 보고서 내용: {s['data']}. 생기부 작성하시오."
            retries = 0
            while retries < 3:
                try:
                    inputs = [s['data'], prompt] if isinstance(s['data'], Image.Image) else prompt
                    response = client.models.generate_content(model='gemini-2.0-flash', contents=inputs)
                    st.text_area(f"{s['id']}번 학생 결과", value=response.text, height=150)
                    time.sleep(15) # 필수 대기
                    break
                except Exception as e:
                    retries += 1
                    if retries < 3: 
                        st.warning(f"서버 지연... 15초 후 재시도({retries}/3)")
                        time.sleep(15)
                    else: st.error(f"{s['id']}번 생성 실패: {e}")
