import streamlit as st
import time
from PIL import Image

try:
    from google import genai
except ImportError:
    genai = None

# 1. 페이지 설정
st.set_page_config(page_title="AI 학교생활기록부 자동화 봇", page_icon="🎓", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# 2. 사용자 인증 (간소화 버전)
ALLOWED_EMAILS = ["akswls1203@gmail.com", "science_teacher@gmail.com", "admin@school.ms.kr"]

def simulate_login(email):
    if email in ALLOWED_EMAILS:
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.rerun()
    elif email == "":
        st.warning("이메일을 입력해주세요.")
    else:
        st.error("허가되지 않은 계정입니다.")

# 3. 로그인 화면
if not st.session_state.logged_in:
    st.title("🔒 학교 전용 특기사항 자동화 봇")
    email_input = st.text_input("Google 이메일 주소 입력")
    if st.button("인증 및 로그인"):
        simulate_login(email_input)
    st.stop()

# 4. 메인 화면
st.title("📝 AI 학교생활기록부 특기사항 작성 도우미")
st.write(f"👤 로그인 계정: **{st.session_state.user_email}**")

# API 설정 (사이드바)
st.sidebar.title("⚙️ API 설정")
api_key_input = st.sidebar.text_input("Gemini API Key", type="password")

client = None
if api_key_input and genai:
    try:
        client = genai.Client(api_key=api_key_input)
    except Exception as e:
        st.sidebar.error(f"API 초기화 실패: {e}")

# 입력 영역
selected_record_type = st.radio("특기사항 종류", ["자율", "동아리", "진로", "세특"], horizontal=True)
activity_name = st.text_input("활동명")
content = st.text_area("활동 내용 및 학생 특징")
uploaded_file = st.file_uploader("보고서 이미지 업로드", type=["jpg", "png"])

image = None
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드 완료", width=300)

# 생성 버튼
if st.button("✨ 생기부 문구 생성"):
    if not client:
        st.error("API Key를 입력해주세요.")
    elif not activity_name or not content:
        st.warning("활동명과 내용을 입력해주세요.")
    else:
        with st.spinner("생성 중..."):
            prompt = f"""
            당신은 베테랑 교사입니다. 다음 규칙을 준수하여 생기부 문구를 작성하세요.
            1. 어조: '~함.', '~임.' 등 명사형 종결어미 사용.
            2. 문체: 학생 이름이나 '이 학생은' 사용 금지, 관찰자 시점 서술.
            3. 규칙: 하나의 문단으로 작성.
            
            [내용]
            - 활동명: {activity_name}
            - 상세: {content}
            """
            
            try:
                if image:
                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=[image, prompt]
                    )
                else:
                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=prompt
                    )
                st.success("완료!")
                st.write(response.text)
            except Exception as e:
                st.error(f"생성 실패: {e}")
