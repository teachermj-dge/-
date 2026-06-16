import streamlit as st
import time
from PIL import Image

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
    st.info("💡 **테스트용 로그인 이메일:** `teacher1@school.ms.kr`")
    
    with st.form("login_form"):
        email_input = st.text_input("Google 이메일 주소 입력")
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

st.sidebar.title("⚙️ API 설정")
api_key_input = st.sidebar.text_input("Gemini API Key 입력", type="password", help="구글 AI 스튜디오에서 발급받은 API 키를 넣어주세요.")

client = None
if api_key_input and genai is not None:
    try:
        client = genai.Client(api_key=api_key_input)
    except Exception as e:
        st.sidebar.error(f"API 초기화 실패: {e}")
else:
    try:
        if "GEMINI_API_KEY" in st.secrets and genai is not None:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            st.sidebar.success("🔑 Streamlit Secrets에서 API 키를 불러왔습니다.")
        else:
            st.sidebar.warning("⚠️ AI 기능을 사용하려면 사이드바에 API Key를 입력하세요.")
    except Exception:
        st.sidebar.warning("⚠️ AI 기능을 사용하려면 사이드바에 API Key를 입력하세요.")

# ==========================================
# 공통 설정 영역 (모든 학생에게 공통 적용)
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
            sel_year = st.selectbox("연도", range(2023, 2031), index=3) # 2026년
        with d_col2:
            sel_month = st.selectbox("월", range(1, 13), format_func=lambda x: f"{x:02d}")
        with d_col3:
            sel_day = st.selectbox("일", range(1, 32), format_func=lambda x: f"{x:02d}")
        activity_date_str = f"{sel_year}.{sel_month:02d}.{sel_day:02d}."

with com_col3:
    target_bytes = st.number_input("목표 분량 (Byte)", min_value=100, max_value=3000, value=900, step=100, help="한글 1자는 약 3Byte로 계산됩니다.")

st.markdown("---")

# ==========================================
# 개별 학생 설정 영역 (1~5명)
# ==========================================
st.markdown("### 👩‍🎓 학생별 정보 입력")
num_students = st.selectbox("입력할 학생 수", [1, 2, 3, 4, 5], help="최대 5명까지 한 번에 생성할 수 있습니다.")

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
                
            uploaded_file = st.file_uploader(f"보고서 이미지 업로드 (선택)", type=["jpg", "jpeg", "png"], key=f"file_{i}")
            img_obj = None
            if uploaded_file is not None:
                try:
                    img_obj = Image.open(uploaded_file)
                    st.success("이미지 로드 완료")
                except Exception:
                    st.error("이미지 로드 오류")
        
        students_data.append({
            "id": i + 1,
            "career": career_path,
            "trait": characteristic,
            "level": achievement_level,
            "img": img_obj
        })

st.markdown("---")

# ==========================================
# 프롬프트 엔지니어링 (핵심 로직)
# ==========================================
def build_prompt(record_type, career, traits, level, act_name, date_text, target_bytes, has_img):
    target_chars = target_bytes // 3 
    
    prompt = (
        "당신은 대한민국의 베테랑 교사이자 생기부 작성의 달인입니다. 제공된 학생 정보와 보고서를 바탕으로 특기사항을 작성하세요.\n\n"
        "[절대 준수 규칙: 문체 및 관점]\n"
        "1. 어조: 모든 문장의 끝맺음은 반드시 '~함.', '~임.', '~밝힘.'과 같은 개조식 명사형 종결어미를 사용하세요.\n"
        "2. 관찰자 시점: 학생의 내면 상태나 감정(예: 인식함, 다짐함, 느낌, 생각함, 깨달음)을 단정지어 서술하지 마세요. 대신 학생의 결과물에 나타난 표현(예: ~라고 서술함, ~의 필요성을 주장함, ~라고 보고서에 작성함, ~방안을 제시함)으로 철저히 교사의 관찰 시점에서 작성하세요.\n"
        "3. AI 말투 금지: '컴퓨터 공학과와 관련된 역량을 바탕으로'와 같은 기계적인 표현을 피하고, 진로와 관련된 '핵심 역량'(예: 컴퓨팅 사고력)이 돋보인다는 식으로 자연스럽게 환원하세요.\n"
        "4. 주어 생략: 첫 문장을 포함하여 모든 문장에서 학생의 이름이나 '이 학생은'과 같은 주어를 절대 사용하지 마세요.\n"
        "5. 단일 문단(줄바꿈 절대 금지): 모든 문장은 중간에 줄바꿈(엔터)을 절대 하지 말고, 처음부터 끝까지 하나의 덩어리(단일 문단)로 쭈욱 이어서 작성하세요.\n"
        "6. 특수문자 금지: 슬래시(/) 등 불필요한 특수 기호를 절대 사용하지 마세요. (예: '유포/악용' 대신 '유포 및 악용' 또는 '유포와 악용'으로 자연스럽게 풀어서 작성)\n\n"
        "[작성 양식 및 예시 (이 호흡과 구조를 똑같이 따라할 것)]\n"
        "양식 구조: '학생 총 평가' - '활동 내용 및 과정' - '활동에 대한 평가'\n"
        "예시 1: 성폭력 예방교육(2026.04.01.)에 적극적으로 참여하며, 디지털 환경 및 시스템에 대한 이해를 바탕으로 공동체 역량을 함양하려는 태도를 보임. 제시된 보고서에서 디지털 성폭력이 시공간 제약 없이 발생하며, 빠른 전파 속도와 익명성으로 인해 연속적이고 집단적인 피해를 초래할 수 있는 특성을 분석함. 장난과 범죄의 경계를 명확히 구분하고, 사이버 공동체의 건전한 문화 조성에 기여하려는 의지를 서술함.\n"
        "예시 2: 과학 탐구 주간(2023.05.08.-2023.07.07.)에서 매질에 따른 소리의 세기 변화를 주제로 탐구를 진행함. 아두이노 회로로 소리의 세기를 측정하는 코드를 작성하고, 진공 챔버 속 매질에 따른 소리의 세기를 비교함. 물리학Ⅰ의 파동 개념을 심화 적용하여 회로 및 코드를 구성하는 과정에서 뛰어난 과학적 개념 적용 능력이 드러남.\n\n"
        f"\n[입력된 데이터 및 조건]\n"
        f"- 작성할 영역: {record_type}\n"
        f"- 목표 분량: {target_bytes} Byte 내외 (공백 포함 한글 약 {target_chars}자 내외에 맞춰 길이를 조절하세요.)\n"
    )
    
    if record_type == "행동특성 및 종합의견":
        prompt += "- [행동특성 특별 규칙]: 교사가 부정적인 특성을 입력했더라도 직접적으로 비판하지 말고 '발전 가능성'이나 '노력하는 성장 과정'으로 긍정적으로 순화하세요.\n"
        
    if act_name:
        if date_text: prompt += f"- 활동명 및 날짜: {act_name}({date_text})\n"
        else: prompt += f"- 활동명: {act_name}\n"
        
    if career: prompt += f"- 진로 희망 분야: {career}\n"
    if traits: prompt += f"- 강조하고자 하는 특성: {traits}\n"
    if level: prompt += f"- 성취수준: {level}\n"
    
    if has_img:
        prompt += "\n[요청]: 첨부된 보고서 이미지의 내용을 꼼꼼히 읽고, 위 예시들의 '활동 내용 및 과정'처럼 구체적인 팩트 위주로 요약하여 문안에 포함시키세요."
    else:
        prompt += "\n[요청]: 첨부된 이미지가 없습니다. 활동명과 특성을 바탕으로 일반적이고 모범적인 활동 과정을 상상하여 서술하세요."
        
    return prompt

if st.button("✨ 생기부 문구 일괄 생성하기", type="primary", use_container_width=True):
    if not client:
        st.error("🔒 왼쪽 사이드바에 Gemini API Key를 입력해야 AI 요청이 가능합니다.")
    elif selected_record_type != "행동특성 및 종합의견" and not activity_name:
        st.warning("⚠️ 활동명을 입력해주세요.")
    else:
        with st.spinner(f"🔮 {num_students}명의 학생 데이터를 분석하여 생기부 문장을 생성하고 있습니다. 잠시만 기다려주세요..."):
            
            results_container = st.container()
            
            for idx, s_data in enumerate(students_data):
                success = False
                retries = 0
                max_retries = 3
                
                while not success and retries < max_retries:
                    try:
                        final_prompt = build_prompt(
                            record_type=selected_record_type,
                            career=s_data["career"],
                            traits=s_data["trait"],
                            level=s_data["level"],
                            act_name=activity_name,
                            date_text=activity_date_str,
                            target_bytes=target_bytes,
                            has_img=(s_data["img"] is not None)
                        )
                        
                        contents = [s_data["img"], final_prompt] if s_data["img"] else final_prompt
                        response = client.models.generate_content(model='gemini-2.5-flash', contents=contents)
                        
                        with results_container:
                            st.success(f"✅ 학생 {s_data['id']} 생성 완료!")
                            cleaned_text = response.text.replace("\n", " ").replace("/", " 및 ").replace("  ", " ").strip()
                            st.text_area(f"학생 {s_data['id']} 결과물", value=cleaned_text, height=150, key=f"res_{s_data['id']}_{retries}")
                        
                        success = True
                        
                        if s_data["id"] != num_students:
                            time.sleep(5)
                            
                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                            retries += 1
                            if retries < max_retries:
                                with results_container:
                                    st.warning(f"⏳ 구글 서버 과부하 방지: 10초 대기 후 학생 {s_data['id']} 재시도 중... ({retries}/{max_retries})")
                                time.sleep(10)
                            else:
                                with results_container:
                                    st.error(f"❌ 학생 {s_data['id']} 생성 실패. 무료 사용 한도가 초과되었습니다. 1~2분 뒤에 다시 눌러주세요.")
                        else:
                            with results_container:
                                st.error(f"❌ 학생 {s_data['id']} 생성 중 오류 발생: {error_msg}")
                            break
