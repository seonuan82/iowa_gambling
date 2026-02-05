"""
Free Recall Task - Recall Session (회상 세션)
Streamlit 기반 심리학 실험 과제

이전 학습 세션에서 제시된 단어를 자유회상
소요시간 측정 + Google Spreadsheet 로깅
"""

import streamlit as st
from datetime import datetime, timezone, timedelta
import time
from free_recall_utils import (
    FreeRecallSession,
    RecallResponse,
    generate_session_id,
    calculate_recall_scores,
    get_fixed_word_list,
)

KST = timezone(timedelta(hours=9))

# Google Spreadsheet 로깅
try:
    from logging_utils import gsheet_log_event
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="단어 기억 과제 - 회상",
    page_icon="📝",
    layout="centered"
)

# CSS 스타일
st.markdown("""
<style>
    .recalled-word {
        display: inline-block;
        padding: 5px 15px;
        margin: 5px;
        background-color: #e9ecef;
        border-radius: 20px;
        font-size: 18px;
    }
    .stButton > button {
        width: 100%;
        font-size: 20px;
        padding: 15px;
    }
    .phase-indicator {
        text-align: center;
        font-size: 14px;
        color: #6c757d;
        padding: 10px;
        border-bottom: 1px solid #dee2e6;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

NEXT_EXPERIMENT_URL = "https://intertemporal-choice-task-5srsbs8qpesspk4szappzmk.streamlit.app/"


def init_session_state():
    """세션 상태 초기화"""
    defaults = {
        'phase': 'setup',
        'session': None,
        'recalled_words_input': [],
        'recall_start_time': None,
        'participant_id': None,
        'logged_end': False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def show_end_screen():
    """종료 화면"""
    st.markdown("## 게임 종료!")
    st.balloons()

    st.markdown("### 실험에 참가해 주셔서 감사합니다.")
    st.markdown("### 아래 버튼을 눌러 다음 실험으로 이동해 주세요.")
    st.markdown("---")

    st.link_button(
        "▶ 다음 실험으로 이동",
        NEXT_EXPERIMENT_URL,
        use_container_width=True
    )


def recall_setup():
    """회상 세션 - 참가자 ID 입력"""
    st.markdown("## 📝 단어 기억 과제 - 회상")
    st.markdown("---")
    st.markdown("""
    ### 과제 설명

    이전에 학습한 단어를 **최대한 많이** 기억해서 입력해주세요.

    - 순서는 상관없습니다.
    - 기억나는 대로 자유롭게 입력하면 됩니다.
    - 정확하지 않아도 괜찮으니, 최대한 많이 기억해보세요.
    """)
    st.markdown("---")

    participant_id = st.text_input(
        "참가자 ID를 입력하세요",
        placeholder="예: P001"
    )

    if st.button("시작하기", type="primary"):
        if participant_id.strip() == "":
            st.warning("참가자 ID를 입력해주세요.")
        else:
            # 고정 단어 목록 (채점용, 순서 무관)
            word_list = get_fixed_word_list(randomize=False)
            st.session_state.session = FreeRecallSession(
                session_id=generate_session_id(),
                participant_id=participant_id,
                condition="mixed",
                processing_type="none",
                start_time=datetime.now(KST).isoformat(),
                num_words=15,
                presentation_duration=2.0,
                distractor_duration=0,
                recall_duration=0,
                presented_words=word_list,
            )
            st.session_state.participant_id = participant_id
            st.session_state.phase = 'recall'
            st.session_state.recall_start_time = time.time()
            st.session_state.recalled_words_input = []

            if LOGGING_AVAILABLE:
                gsheet_log_event(
                    text="Recall session started",
                    user_id=participant_id,
                    event_type="RecallStart"
                )
            st.rerun()


def recall_phase():
    """회상 단계"""
    st.markdown(
        '<div class="phase-indicator">회상 단계 | 기억나는 단어를 입력하세요</div>',
        unsafe_allow_html=True
    )

    # 경과 시간
    if st.session_state.recall_start_time:
        elapsed = int(time.time() - st.session_state.recall_start_time)
        st.caption(f"경과 시간: {elapsed}초")

    st.markdown("---")
    st.markdown("### 기억나는 단어를 입력하세요")
    st.markdown("*순서는 상관없습니다. 한 단어씩 입력 후 '추가' 버튼을 누르세요.*")

    # 입력된 단어들 표시
    if st.session_state.recalled_words_input:
        st.markdown("**입력한 단어:**")
        words_html = ""
        for w in st.session_state.recalled_words_input:
            words_html += f'<span class="recalled-word">{w}</span>'
        st.markdown(words_html, unsafe_allow_html=True)
        st.markdown(f"총 {len(st.session_state.recalled_words_input)}개 입력됨")

    st.markdown("---")

    # 단어 입력
    col1, col2 = st.columns([3, 1])
    with col1:
        word_input = st.text_input(
            "단어 입력",
            placeholder="기억나는 단어를 입력하세요",
            key="recall_input",
            label_visibility="collapsed"
        )
    with col2:
        if st.button("추가", key="add_word", use_container_width=True):
            if word_input and word_input.strip():
                word = word_input.strip()
                if word not in st.session_state.recalled_words_input:
                    st.session_state.recalled_words_input.append(word)
                    st.rerun()

    st.markdown("---")

    if st.button("회상 완료", type="primary"):
        finish_recall()
        st.rerun()


def finish_recall():
    """회상 완료 처리 및 Google Spreadsheet 로깅"""
    session = st.session_state.session

    # 소요시간 계산
    duration_seconds = None
    if st.session_state.recall_start_time:
        duration_seconds = time.time() - st.session_state.recall_start_time

    # 제시된 단어 집합
    presented_words = {w.word: w for w in session.presented_words}

    # 회상 응답 기록
    for i, word in enumerate(st.session_state.recalled_words_input):
        is_correct = word in presented_words
        is_intrusion = not is_correct

        original_position = None
        if is_correct:
            original_position = presented_words[word].presentation_order

        response = RecallResponse(
            recalled_word=word,
            recall_order=i + 1,
            response_time=0,
            is_correct=is_correct,
            is_intrusion=is_intrusion,
            original_position=original_position
        )
        session.recalled_words.append(response)

    session.end_time = datetime.now(KST).isoformat()

    # 점수 계산
    scores = calculate_recall_scores(session)

    # Google Spreadsheet 로깅 (한 번만)
    if LOGGING_AVAILABLE and not st.session_state.logged_end:
        duration_str = ""
        if duration_seconds is not None:
            minutes = int(duration_seconds) // 60
            secs = int(duration_seconds) % 60
            duration_str = f", Duration: {minutes}m{secs:02d}s ({duration_seconds:.1f}s)"

        recalled_list = ", ".join(
            st.session_state.recalled_words_input
        ) if st.session_state.recalled_words_input else "(none)"

        summary = (
            f"Recall completed - "
            f"Correct: {scores['correct_recalls']}/{scores['total_presented']}, "
            f"Rate: {scores['recall_rate']:.1%}, "
            f"Intrusions: {scores['intrusion_errors']}, "
            f"Pos:{scores['category_recall']['positive']} "
            f"Neg:{scores['category_recall']['negative']} "
            f"Neu:{scores['category_recall']['neutral']}"
            f"{duration_str}, "
            f"Words: [{recalled_list}]"
        )
        gsheet_log_event(
            text=summary,
            user_id=st.session_state.participant_id,
            event_type="RecallEnd"
        )
        st.session_state.logged_end = True

    st.session_state.phase = 'end'


def main():
    """메인 함수"""
    init_session_state()

    phase = st.session_state.phase

    if phase == 'setup':
        recall_setup()
    elif phase == 'recall':
        recall_phase()
    elif phase == 'end':
        show_end_screen()


if __name__ == "__main__":
    main()

