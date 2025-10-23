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
SAMPLE_REPORT = (
    "우리 팀은 기후 변화로 인한 이상기온과 자연재해 발생을 예측하기 위해 인공지능 기술을 활용한 프로젝트를 진행하였다. "
    "먼저 지난 20년간의 국내외 기상 데이터를 수집하여 평균 기온, 강수량, 이산화탄소 농도 등의 주요 변수를 정리하였다. "
    "이후 데이터를 학습시키기 위해 Python과 TensorFlow를 활용하여 기온 예측 모델을 설계하였다. 초기에는 단순 선형회귀를 적용했지만 예측 오차가 컸기 때문에, "
    "다층 퍼셉트론(MLP) 모델로 구조를 바꾸고 학습률과 은닉층 수를 조정하면서 정확도를 높였다. 또한 기상청 오픈데이터 API를 통해 실시간 데이터를 추가로 받아 "
    "모델이 새로운 입력에도 대응할 수 있도록 했다. 모델 학습 결과, 평균 제곱 오차(MSE)가 0.15로 줄어들며 성능이 향상되었고, 시각화를 통해 특정 지역의 온도 상승 추세를 "
    "확인할 수 있었다. 예를 들어, 서울과 강릉 지역은 지난 10년간 여름철 평균기온이 꾸준히 상승하는 경향을 보였고, 우리 모델은 향후 5년간 평균기온이 약 1.2도 상승할 것으로 "
    "예측했다. 프로젝트 후반부에는 단순한 예측을 넘어 ‘기후 행동’으로의 연결을 고민하였다. 우리는 예측 결과를 바탕으로 지역별 온실가스 감축 시나리오를 제안하고, 이를 시각화 "
    "대시보드로 구현하였다. Streamlit을 이용해 누구나 접근 가능한 웹 형태로 배포했으며, 이를 통해 학급 친구들이 자신의 지역 데이터를 직접 탐색하고 기후 변화의 심각성을 "
    "체감할 수 있도록 했다. 이번 활동을 통해 우리는 인공지능이 단순한 기술이 아니라 사회 문제 해결의 강력한 도구가 될 수 있음을 배웠다. 또한 데이터의 품질과 전처리 과정의 "
    "중요성을 실감했으며, 앞으로는 더 다양한 기후 변수와 지역 데이터를 반영하여 예측의 정확도를 높이고 싶다. 무엇보다 협업 과정에서 각자의 역할을 책임감 있게 수행하는 것이 "
    "프로젝트 성공의 핵심이라는 점을 깨달았다."
)

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
