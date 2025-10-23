import textwrap
import streamlit as st
from openai import OpenAI

# ---------------------------
# 기본 설정
# ---------------------------
st.set_page_config(page_title="학생 프로젝트 보고서 요약+세특 생성기", page_icon="🎓", layout="wide")
st.title("🎓 학생 프로젝트 보고서 요약+세특 자동 생성기")
st.caption("보고서 요약 → 관점 요약 → 세부능력 및 특기사항(세특) 자동 문장 생성")

client = OpenAI(api_key=st.secrets["openai_api_key"])

# 샘플 보고서
SAMPLE_REPORT = """우리 팀은 기후 변화 예측을 위해 인공지능 기술을 활용한 프로젝트를 진행하였다... (중략)"""

# ---------------------------
# 세션 상태
# ---------------------------
if "report_input" not in st.session_state:
    st.session_state.report_input = ""
if "selected_question" not in st.session_state:
    st.session_state.selected_question = None
if "q_summary" not in st.session_state:
    st.session_state.q_summary = ""

# ---------------------------
# 사이드바 옵션
# ---------------------------
with st.sidebar:
    st.header("⚙️ 옵션")
    model = st.selectbox("모델 선택", ["gpt-4o-mini", "gpt-4o"], index=0)
    temperature = st.slider("창의성(temperature)", 0.0, 1.0, 0.3, 0.05)
    st.caption("※ 세특 문장은 0.3~0.5 권장")

# ---------------------------
# 함수 정의
# ---------------------------
def summarize_with_limit(report: str, limit: int, teacher_hint: str | None = None) -> str:
    """요약 (기존)"""
    base_prompt = (
        "다음은 고등학생의 프로젝트 활동 보고서입니다.\n"
        "지시에 따라 한국어로 요약하세요.\n\n"
        "규칙:\n"
        "1) 한 단락으로 작성\n"
        "2) 새로운 사실 추가 금지\n"
        "3) 목적→과정→성과→배운 점 순으로 간결히\n"
        f"4) 공백 포함 {limit}자 이내\n"
    )
    if teacher_hint:
        base_prompt += f"\n교사 관점: '{teacher_hint}' 중심으로 관련 내용만 요약.\n"
    resp = client.responses.create(
        model=model,
        input=base_prompt + "\n\n[보고서]\n" + report,
        temperature=float(temperature),
    )
    return resp.output_text.strip()

def generate_se_teuk(q_summary: str, teacher_hint: str) -> str:
    """🆕 세특 자동 문장 생성"""
    prompt = f"""
다음은 학생의 프로젝트 보고서 요약입니다.
이를 바탕으로 생활기록부의 세부능력 및 특기사항(세특)에 들어갈 문장을 생성하세요.

[요약 내용]
{q_summary}

[교사 관점]
{teacher_hint}

규칙:
1. 한 문단 3~5문장 이내.
2. '~함', '~임', '~함으로써' 등 객관적 서술체.
3. 구체적 활동·역할·결과 중심.
4. '~에 관심을 보임' '~의 필요성을 인식함' 같은 표현 금지.
5. 교사가 작성한 것처럼 완성도 있게.
출력은 한 단락만.
"""
    resp = client.responses.create(model=model, input=prompt, temperature=float(temperature))
    return resp.output_text.strip()

# ---------------------------
# 입력
# ---------------------------
st.subheader("1️⃣ 학생 프로젝트 보고서 입력")
use_sample = st.checkbox("샘플 보고서 사용", value=False)
if use_sample:
    st.session_state.report_input = SAMPLE_REPORT

report = st.text_area(
    "보고서 본문", key="report_input",
    height=300, placeholder="학생이 작성한 프로젝트 보고서를 붙여넣으세요."
)

# ---------------------------
# 관점 선택 및 요약
# ---------------------------
st.subheader("2️⃣ 교사 관점 선택 및 관점 요약")

teacher_hints = [
    "데이터 전처리의 타당성 중심",
    "모델 선택과 성능 향상 과정 중심",
    "협업 과정의 역할 분담 중심",
    "성과 지표의 신뢰도와 한계 중심",
    "사회문제 해결 기여 중심"
]

st.session_state.selected_question = st.selectbox(
    "관점 선택", teacher_hints, index=0
)

if st.button("관점 요약 생성", type="primary"):
    if not report.strip():
        st.warning("보고서를 입력하세요.")
    else:
        with st.spinner("관점 요약 생성 중..."):
            q_sum = summarize_with_limit(report, 400, st.session_state.selected_question)
            st.session_state.q_summary = q_sum
            st.success("관점 요약 생성 완료!")
            st.text_area("📘 관점 요약 결과", q_sum, height=180)

# ---------------------------
# 🆕 세특 자동 문장 생성
# ---------------------------
st.subheader("3️⃣ 세부능력 및 특기사항(세특) 자동 생성")

if st.session_state.q_summary:
    if st.button("세특 문장 생성 ✨", type="primary"):
        with st.spinner("세특 문장 생성 중..."):
            try:
                se_teuk = generate_se_teuk(
                    st.session_state.q_summary,
                    st.session_state.selected_question
                )
                st.success("세특 문장 생성 완료!")
                st.text_area("📗 세특 문장", se_teuk, height=180)
                st.download_button(
                    "📥 세특 문장 다운로드 (txt)",
                    data=se_teuk.encode("utf-8-sig"),
                    file_name="세특_자동생성.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"세특 생성 중 오류: {e}")
else:
    st.info("먼저 관점 요약을 생성하세요.")

# ---------------------------
# 푸터
# ---------------------------
st.divider()
st.caption("© 2025 AI 기반 학생 보고서 요약 + 세특 자동 생성기 | by 멋짐")
