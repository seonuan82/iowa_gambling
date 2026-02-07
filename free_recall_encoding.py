"""
Free Recall Task - Encoding Session (학습 세션)
Streamlit 기반 심리학 실험 과제

단순암기 / 긍정·부정·중립 혼합 / 15개 단어 / 2초 제시
"""

import streamlit as st
from datetime import datetime, timezone, timedelta
import time
from free_recall_utils import (
    FreeRecallSession,
    generate_session_id,
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
    page_title="단어 기억 과제 - 학습",
    page_icon="📝",
    layout="centered"
)

# CSS 스타일
st.markdown("""
<style>
    .word-display {
        font-size: 72px;
        font-weight: bold;
        text-align: center;
        padding: 100px 0;
        font-family: 'Malgun Gothic', sans-serif;
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

NEXT_EXPERIMENT_URL = "https://iowagambling-101.streamlit.app/"


def init_session_state():
    """세션 상태 초기화"""
    defaults = {
        'phase': 'setup',
        'session': None,
        'current_word_idx': 0,
        'word_start_time': None,
        'participant_id': None,
        'logged_end': False,
        'encoding_start_time': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    """메인 함수"""
    init_session_state()

    phase = st.session_state.phase

    # 전체 페이지를 단일 placeholder로 관리
    page = st.empty()

    if phase == 'setup':
        with page.container():
            st.markdown("## 📝 단어 기억 과제 - 학습")
            st.markdown("---")
            st.markdown("""
            ### 과제 설명

            화면에 단어가 하나씩 나타납니다.
            각 단어를 **잘 기억해주세요.**

            나중에 기억나는 단어를 모두 입력하게 됩니다.
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
                    word_list = get_fixed_word_list(randomize=True)
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
                    st.session_state.phase = 'encoding'
                    st.session_state.current_word_idx = -1
                    st.session_state.encoding_start_time = time.time()
                    st.session_state.word_start_time = time.time()

                    if LOGGING_AVAILABLE:
                        gsheet_log_event(
                            text="Encoding session started - 15 words, 2s each, mixed",
                            user_id=participant_id,
                            event_type="EncodingStart"
                        )
                    page.empty()
                    st.rerun()

    elif phase == 'encoding':
        session = st.session_state.session
        current_idx = st.session_state.current_word_idx

        with page.container():
            if current_idx == -1:
                # 2초 대기 화면
                st.markdown(
                    '<div class="phase-indicator">학습 단계 준비 중...</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    '<div class="word-display" style="color: #888;">잠시 후 단어가 나타납니다</div>',
                    unsafe_allow_html=True
                )
            elif current_idx < len(session.presented_words):
                # 단어 표시
                st.markdown(
                    f'<div class="phase-indicator">학습 단계 | 단어 {current_idx + 1} / {session.num_words}</div>',
                    unsafe_allow_html=True
                )
                st.progress((current_idx + 1) / session.num_words)
                word = session.presented_words[current_idx]
                st.markdown(
                    f'<div class="word-display">{word.word}</div>',
                    unsafe_allow_html=True
                )

        # 로직 처리
        if current_idx == -1:
            elapsed = time.time() - st.session_state.encoding_start_time
            if elapsed >= 2.0:
                st.session_state.current_word_idx = 0
                st.session_state.word_start_time = time.time()
            time.sleep(0.5)
            page.empty()
            st.rerun()

        elif current_idx >= len(session.presented_words):
            session.end_time = datetime.now().isoformat()
            if LOGGING_AVAILABLE:
                gsheet_log_event(
                    text="Encoding session completed",
                    user_id=st.session_state.participant_id,
                    event_type="EncodingEnd"
                )
            st.session_state.phase = 'end'
            page.empty()
            st.rerun()

        else:
            elapsed = time.time() - st.session_state.word_start_time
            remaining = max(0, session.presentation_duration - elapsed)
            if remaining <= 0:
                st.session_state.current_word_idx += 1
                st.session_state.word_start_time = time.time()
            time.sleep(0.5)
            page.empty()
            st.rerun()

    elif phase == 'end':
        with page.container():
            st.markdown("## 학습 완료!")
            st.balloons()
            st.markdown("### 실험에 참가해 주셔서 감사합니다.")
            st.markdown("### 아래 버튼을 눌러 다음 실험으로 이동해 주세요.")
            st.markdown("---")
            st.link_button(
                "▶ 다음 실험으로 이동",
                NEXT_EXPERIMENT_URL,
                use_container_width=True
            )


if __name__ == "__main__":
    main()

