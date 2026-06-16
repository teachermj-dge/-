import streamlit as st
import time
from PIL import Image
import PyPDF2  # PDF 처리를 위해 추가

try:
    from google import genai
except ImportError:
    genai = None

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(page_title="AI 학교생활기록부 자동화 봇", page_icon="🎓", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# ==========================================
# 2. 사용자 인증 및 화이트리스트
# ==========================================
ALLOWED_EMAILS = ["teacher1@school.ms.kr", "science_teacher@gmail.com", "admin@school.ms.kr"]

def simulate_login(email):
    if email in ALLOWED_EMAILS:
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.success(f"로그인 성공! 환영합니다, {email} 선생님.")
        st.rerun()
    elif email == "":
        st.warning("이메일을 입력해주세요.")
    else:
        st.error(f"로그인 실패: {email}은(는) 허가되지 않은 계정입니다.")

def logout():
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.rerun()

# ==========================================
# 3. 로그인 화면 구현
# ==========================================
if not st.session_state.logged_in:
    st.title("🔒 학교 전용 특기사항 자동화 봇")
    st.markdown("우리 학교 교직원 계정으로 로그인 후 사용 가능합니다.")
    st.info("💡 **안내:** 허가된 이메일 주소를 입력해 주세요.")
    
    with st.form("login_form"):
        email_input = st.text_input("이메일 주소 입력")
        submit_button = st.form_submit_button("인증 및 로그인")
        if submit_button:
            simulate_login(email_input)
    st.stop()

# ==========================================
# 4. 메인 애플리케이션 화면
# ==========================================
col_title, col_user = st.columns([8, 2])
with col_title:
    st.title("📝 AI 학교생활기록부 특기사항 작성 도우미")
with col_user:
    st.write(f"👤 **{st.session_state.user_email}**")
    if st.button("로그아웃", type="secondary"):
         logout()

st.markdown("---")

client = None
try:
    if "GEMINI_API_KEY" in st.secrets and genai is not None:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("⚠️ 관리자 설정 오류: 시스템에 API 키가 등록되지 않았습니다.")
except Exception:
    st.error("⚠️ 관리자 설정 오류: 시스템에 API 키가 등록되지 않았습니다.")

# ==========================================
# 공통 설정 영역
# ==========================================
st.markdown("### 📌 공통 설정 (활동 정보 및 분량)")
record_types = ["자율 활동 특기 사항", "동아리 활동 특기 사항", "진로 활동 특기 사항", "과목 별 세부 능력 및 특기 사항", "행동특성 및 종합의견"]
selected_record_type = st.radio("작성할 특기사항 종류:", record_types, horizontal=True)

com_col1, com_col2, com_col3 = st.columns([2, 2, 1])
with com_col1:
    if selected_record_type == "행동특성 및 종합의견":
        activity_name = st.text_input("주요 활동이나 계기 (선택 사항)", placeholder="예: 학급 반장, 1학기 학교생활 전반 등")
    else:
        activity_name = st.text_input("활동명 (필수)", placeholder="예: 과학 탐구 주간, 시사탐구활동")

with com_col2:
    use_date = st.checkbox("날짜 입력하기", value=True)
    activity_date_str = ""
    if use_date:
        d_col1, d_col2, d_col3 = st.columns(3)
        with d_col1:
            sel_year = st.selectbox("연도", range(2023, 2031), index=3)
        with d_col2:
            sel_month = st.selectbox("월", range(1, 13), format_func=lambda x: f"{x:02d}")
        with d_col3:
            sel_day = st.selectbox("일", range(1, 32), format_func=lambda x: f"{x:02d}")
        activity_date_str = f"{sel_year}.{sel_month:02d}.{sel_day:02d}."

with com_col3:
    target_bytes = st.number_input("목표 분량 (Byte)", min_value=100, max_value=3000, value=900, step=100)

st.markdown("---")

# ==========================================
# 개별 학생 설정 영역
# ==========================================
st.markdown("### 👩‍🎓 학생별 정보 입력")
num_students = st.selectbox("입력할 학생 수", [1, 2, 3], help="안정적인 생성을 위해 한 번에 최대 3명까지만 가능합니다.")

students_data = []
tabs = st.tabs([f"학생 {i+1}" for i in range(num_students)])

for i, tab in enumerate(tabs):
    with tab:
        st.markdown(f"**[학생 {i+1} 정보]**")
        col_in1, col_in2 = st.columns(2)
        
        with col_in1:
            career_path = st.text_input("진로 희망 분야", placeholder="예: 컴퓨터 공학, 기계공학", key=f"career_{i}")
            characteristic = st.text_input("강조하고자 하는 특성", placeholder="예: 문제해결력, 책임감", key=f"char_{i}")
        
        with col_in2:
            achievement_level = None
            if selected_record_type not in ["동아리 활동 특기 사항", "행동특성 및 종합의견"]:
                achievement_level = st.selectbox("성취수준", ["선택 안 함", "상", "중", "하"], key=f"level_{i}")
                if achievement_level == "선택 안 함": achievement_level = None
            
            # PDF 및 이미지 업로드 통합
            uploaded_file = st.file_uploader(f"보고서/PDF 업로드 (선택)", type=["jpg", "jpeg", "png", "pdf"], key=f"file_{i}")
            file_content = None # 이미지 객체 또는 PDF 텍스트 저장용
            
            if uploaded_file is not None:
                if uploaded_file.type == "application/pdf":
                    try:
                        reader = PyPDF2.PdfReader(uploaded_file)
                        file_content = "".join([page.extract_text() or "" for page in reader.pages])
                        st.info("📄 PDF 텍스트 추출 완료")
                    except Exception:
                        st.error("PDF 읽기 오류")
                else:
                    try:
                        file_content = Image.open(uploaded_file)
                        st.success("📷 이미지 로드 완료")
                    except Exception:
                        st.error("이미지 로드 오류")
        
        students_data.append({
            "id": i + 1,
            "career": career_path,
            "trait": characteristic,
            "level": achievement_level,
            "content": file_content # 이미지 혹은 텍스트가 저장됨
        })

st.markdown("---")

# ==========================================
# 프롬프트 엔지니어링 및 생성 로직
# ==========================================
def build_prompt(record_type, career, traits, level, act_name, date_text, target_bytes, content_type):
    target_chars = target_bytes // 3 
    prompt = (
        "당신은 대한민국의 베테랑 교사이자 생기부 작성의 달인입니다. 제공된 학생 정보와 보고서를 바탕으로 특기사항을 작성하세요.\n\n"
        "[절대 준수 규칙: 문체 및 관점]\n"
        "1. 어조: 모든 문장의 끝맺음은 반드시 '~함.', '~임.', '~밝힘.'과 같은 개조식 명사형 종결어미를 사용하세요.\n"
        "2. 관찰자 시점: 학생의 내면 상태나 감정(예: 인식함, 다짐함, 느낌)을 단정지어 서술하지 마세요.\n"
        "3. AI 말투 금지: '핵심 역량'이 돋보인다는 식으로 자연스럽게 환원하세요.\n"
        "4. 주어 생략: 학생의 이름이나 '이 학생은'과 같은 주어를 절대 사용하지 마세요.\n"
        "5. 단일 문단: 줄바꿈 없이 하나의 덩어리로 작성하세요.\n"
        f"\n[입력된 데이터 및 조건]\n"
        f"- 작성할 영역: {record_type}\n"
        f"- 목표 분량: {target_bytes} Byte 내외\n"
    )
    if act_name: prompt += f"- 활동명: {act_name}({date_text})\n" if date_text else f"- 활동명: {act_name}\n"
    if career: prompt += f"- 진로 희망 분야: {career}\n"
    if traits: prompt += f"- 강조하고자 하는 특성: {traits}\n"
    if level: prompt += f"- 성취수준: {level}\n"
    
    if content_type == "pdf":
        prompt += "\n[요청]: 첨부된 보고서 텍스트 내용을 구체적인 팩트 위주로 요약하여 문안에 포함시키세요."
    elif content_type == "image":
        prompt += "\n[요청]: 첨부된 이미지의 내용을 위 예시들처럼 구체적인 팩트 위주로 요약하여 문안에 포함시키세요."
    else:
        prompt += "\n[요청]: 활동명과 특성을 바탕으로 모범적인 활동 과정을 상상하여 서술하세요."
    return prompt

if st.button("✨ 생기부 문구 일괄 생성하기", type="primary", use_container_width=True):
    if not client:
        st.error("🔒 시스템 설정 오류: API 키가 등록되지 않아 생성할 수 없습니다.")
    elif selected_record_type != "행동특성 및 종합의견" and not activity_name:
        st.warning("⚠️ 활동명을 입력해주세요.")
    else:
        with st.spinner(f"🔮 {num_students}명의 데이터를 분석하고 있습니다..."):
            results_container = st.container()
            for s_data in students_data:
                success = False
                retries = 0
                while not success and retries < 3:
                    try:
                        # 데이터 타입 판별
                        content_type = "none"
                        contents_for_api = []
                        if isinstance(s_data["content"], str): # PDF 텍스트
                            content_type = "pdf"
                            final_prompt = build_prompt(selected_record_type, s_data["career"], s_data["trait"], s_data["level"], activity_name, activity_date_str, target_bytes, content_type)
                            contents_for_api = f"{final_prompt}\n\n보고서 내용: {s_data['content']}"
                        elif isinstance(s_data["content"], Image.Image): # 이미지
                            content_type = "image"
                            final_prompt = build_prompt(selected_record_type, s_data["career"], s_data["trait"], s_data["level"], activity_name, activity_date_str, target_bytes, content_type)
                            contents_for_api = [s_data["content"], final_prompt]
                        else: # 데이터 없음
                            contents_for_api = build_prompt(selected_record_type, s_data["career"], s_data["trait"], s_data["level"], activity_name, activity_date_str, target_bytes, content_type)
                        
                        response = client.models.generate_content(model='gemini-2.0-flash', contents=contents_for_api)
                        
                        with results_container:
                            st.success(f"✅ 학생 {s_data['id']} 생성 완료!")
                            cleaned_text = response.text.replace("\n", " ").replace("/", " 및 ").strip()
                            st.text_area(f"학생 {s_data['id']} 결과물", value=cleaned_text, height=150, key=f"res_{s_data['id']}_{retries}")
                        success = True
                        if s_data["id"] != num_students: time.sleep(15) # 필수 대기
                    except Exception as e:
                        retries += 1
                        if retries < 3:
                            with results_container: st.warning(f"⏳ 구글 서버 지연: 15초 대기 후 재시도 중... ({retries}/3)")
                            time.sleep(15)
                        else:
                            with results_container: st.error(f"❌ 학생 {s_data['id']} 생성 실패: {e}")
