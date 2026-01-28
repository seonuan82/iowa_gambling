"""
Free Recall Task (자유회상 과제)
Streamlit 기반 심리학 실험 과제

단어목록 자유회상 패러다임
- 단어 제시 → 방해과제 → 자유회상
"""

import streamlit as st
from datetime import datetime
import time
from free_recall_utils import (
    WordListManager,
    FreeRecallSession,
    RecallResponse,
    generate_session_id,
    calculate_recall_scores,
    prepare_for_spreadsheet,
    generate_math_problem
)

# 페이지 설정
st.set_page_config(
    page_title="단어 기억 과제",
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
    .fixation {
        font-size: 72px;
        text-align: center;
        padding: 100px 0;
        color: #666;
    }
    .timer-display {
        font-size: 36px;
        text-align: center;
        color: #dc3545;
        font-weight: bold;
    }
    .math-problem {
        font-size: 48px;
        text-align: center;
        padding: 30px;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin: 20px 0;
        color: #1a1a1a;
    }
    .recall-input {
        font-size: 24px;
    }
    .recalled-word {
        display: inline-block;
        padding: 5px 15px;
        margin: 5px;
        background-color: #e9ecef;
        border-radius: 20px;
        font-size: 18px;
    }
    .correct-word {
        background-color: #d4edda;
        color: #155724;
    }
    .intrusion-word {
        background-color: #f8d7da;
        color: #721c24;
    }
    .result-metric {
        text-align: center;
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin: 10px 0;
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


def init_session_state():
    """세션 상태 초기화"""
    defaults = {
        'phase': 'setup',  # setup, encoding, distractor, recall, results
        'session': None,
        'word_manager': None,
        'current_word_idx': 0,
        'word_start_time': None,
        'recalled_words_input': [],
        'recall_start_time': None,
        'distractor_start_time': None,
        'math_problem': None,
        'math_answer': None,
        'processing_response': None,  # 처리수준 과제 응답
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def show_setup():
    """실험 설정 화면"""
    st.markdown("## 단어 기억 과제")
    st.markdown("---")

    st.markdown("""
    ### 과제 설명

    이 과제는 **단어 기억력**을 측정하는 실험입니다.

    **진행 순서:**
    1. **단어 학습**: 화면에 단어가 하나씩 나타납니다. 각 단어를 잘 기억해주세요.
    2. **방해 과제**: 간단한 산수 문제를 풀게 됩니다.
    3. **회상 단계**: 기억나는 단어를 모두 입력해주세요. 순서는 상관없습니다.

    **중요:**
    - 단어가 나타나면 집중해서 봐주세요.
    - 회상할 때는 기억나는 대로 자유롭게 입력하면 됩니다.
    - 정확하지 않아도 괜찮으니, 최대한 많이 기억해보세요.
    """)

    st.markdown("---")
    st.markdown("### 실험 설정")

    col1, col2 = st.columns(2)

    with col1:
        participant_id = st.text_input(
            "참가자 ID",
            placeholder="예: P001",
            key="participant_input"
        )

        condition = st.selectbox(
            "단어 유형",
            options=[
                ("mixed", "혼합 (긍정/부정/중립)"),
                ("emotional", "정서 단어 (긍정/부정)"),
                ("neutral", "중립 단어")
            ],
            format_func=lambda x: x[1],
            key="condition_select"
        )

    with col2:
        processing_type = st.selectbox(
            "처리 수준 조건",
            options=[
                ("none", "없음 (단순 암기)"),
                ("semantic", "의미 판단 (이 단어가 좋은 느낌인가요?)"),
                ("perceptual", "외형 판단 (이 단어에 받침이 있나요?)")
            ],
            format_func=lambda x: x[1],
            key="processing_select"
        )

        num_words = st.slider(
            "단어 개수",
            min_value=10,
            max_value=20,
            value=15,
            key="num_words_slider"
        )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        presentation_duration = st.number_input(
            "단어 제시 시간 (초)",
            min_value=1.0,
            max_value=5.0,
            value=2.0,
            step=0.5,
            key="presentation_duration"
        )
    with col2:
        distractor_duration = st.number_input(
            "방해과제 시간 (초)",
            min_value=15,
            max_value=120,
            value=30,
            step=15,
            key="distractor_duration"
        )
    with col3:
        st.markdown("**회상 시간**")
        st.caption("제한 없음 (참여자가 완료 버튼을 누를 때까지)")
        recall_duration = 0

    st.markdown("---")

    if st.button("실험 시작", type="primary", disabled=not participant_id):
        start_experiment(
            participant_id=participant_id,
            condition=condition[0],
            processing_type=processing_type[0],
            num_words=num_words,
            presentation_duration=presentation_duration,
            distractor_duration=int(distractor_duration),
            recall_duration=int(recall_duration)
        )
        st.rerun()


def start_experiment(
    participant_id: str,
    condition: str,
    processing_type: str,
    num_words: int,
    presentation_duration: float,
    distractor_duration: int,
    recall_duration: int
):
    """실험 시작"""
    st.session_state.word_manager = WordListManager()

    # 단어 목록 생성
    word_list = st.session_state.word_manager.create_word_list(
        condition=condition,
        num_words=num_words
    )

    # 세션 생성
    st.session_state.session = FreeRecallSession(
        session_id=generate_session_id(),
        participant_id=participant_id,
        condition=condition,
        processing_type=processing_type,
        start_time=datetime.now().isoformat(),
        num_words=num_words,
        presentation_duration=presentation_duration,
        distractor_duration=distractor_duration,
        recall_duration=recall_duration,
        presented_words=word_list
    )

    st.session_state.phase = 'encoding'
    st.session_state.current_word_idx = 0
    st.session_state.word_start_time = time.time()


def show_encoding():
    """단어 학습 단계"""
    session = st.session_state.session
    current_idx = st.session_state.current_word_idx

    # 진행 표시
    st.markdown(
        f'<div class="phase-indicator">학습 단계 | 단어 {current_idx + 1} / {session.num_words}</div>',
        unsafe_allow_html=True
    )

    # 진행률
    progress = (current_idx + 1) / session.num_words
    st.progress(progress)

    if current_idx < len(session.presented_words):
        word = session.presented_words[current_idx]

        # 단어 표시
        st.markdown(
            f'<div class="word-display">{word.word}</div>',
            unsafe_allow_html=True
        )

        # 처리수준 과제
        processing_type = session.processing_type

        if processing_type == "semantic":
            st.markdown("---")
            st.markdown("### 이 단어가 좋은 느낌인가요?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("예 (좋은 느낌)", key=f"yes_{current_idx}", use_container_width=True):
                    st.session_state.processing_response = "yes"
                    advance_word()
                    st.rerun()
            with col2:
                if st.button("아니오 (좋지 않은 느낌)", key=f"no_{current_idx}", use_container_width=True):
                    st.session_state.processing_response = "no"
                    advance_word()
                    st.rerun()

        elif processing_type == "perceptual":
            st.markdown("---")
            st.markdown("### 이 단어의 첫 글자에 받침이 있나요?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("예 (받침 있음)", key=f"yes_{current_idx}", use_container_width=True):
                    st.session_state.processing_response = "yes"
                    advance_word()
                    st.rerun()
            with col2:
                if st.button("아니오 (받침 없음)", key=f"no_{current_idx}", use_container_width=True):
                    st.session_state.processing_response = "no"
                    advance_word()
                    st.rerun()

        else:  # none - 자동 진행
            # 시간 경과 확인
            elapsed = time.time() - st.session_state.word_start_time
            remaining = max(0, session.presentation_duration - elapsed)

            st.markdown(f"*{remaining:.1f}초 후 다음 단어*")

            if remaining <= 0:
                advance_word()
                st.rerun()
            else:
                # 자동 새로고침 (fragment로 부분 갱신)
                placeholder = st.empty()
                time.sleep(0.5)
                st.rerun()


def advance_word():
    """다음 단어로 진행"""
    st.session_state.current_word_idx += 1
    st.session_state.word_start_time = time.time()
    st.session_state.processing_response = None

    # 모든 단어 완료 시
    if st.session_state.current_word_idx >= st.session_state.session.num_words:
        st.session_state.phase = 'distractor'
        problem, answer = generate_math_problem()
        st.session_state.math_problem = problem
        st.session_state.math_answer = answer
        st.session_state.distractor_start_time = time.time()


def show_distractor():
    """방해과제 단계 (산수)"""
    session = st.session_state.session
    elapsed = time.time() - st.session_state.distractor_start_time
    remaining = max(0, session.distractor_duration - elapsed)

    # 진행 표시
    st.markdown(
        f'<div class="phase-indicator">잠시 쉬어가기 | 산수 문제를 풀어주세요</div>',
        unsafe_allow_html=True
    )

    # 타이머
    st.markdown(
        f'<div class="timer-display">남은 시간: {int(remaining)}초</div>',
        unsafe_allow_html=True
    )

    st.progress(1 - (remaining / session.distractor_duration))

    if remaining <= 0:
        # 회상 단계로 전환
        st.session_state.phase = 'recall'
        st.session_state.recall_start_time = time.time()
        st.session_state.recalled_words_input = []
        st.rerun()

    # 산수 문제
    st.markdown("---")
    st.markdown(
        f'<div class="math-problem">{st.session_state.math_problem}</div>',
        unsafe_allow_html=True
    )

    # 답 입력
    answer_input = st.number_input(
        "답을 입력하세요",
        min_value=0,
        max_value=999,
        step=1,
        key="math_input"
    )

    if st.button("확인", key="submit_math"):
        session.distractor_total += 1
        if answer_input == st.session_state.math_answer:
            session.distractor_correct += 1
            st.success("정답입니다!")
        else:
            st.error(f"오답입니다. 정답: {st.session_state.math_answer}")

        # 새 문제 생성
        problem, answer = generate_math_problem()
        st.session_state.math_problem = problem
        st.session_state.math_answer = answer
        time.sleep(0.5)
        st.rerun()

    # 자동 새로고침
    time.sleep(1)
    st.rerun()


def show_recall():
    """회상 단계"""
    session = st.session_state.session

    # 진행 표시
    st.markdown(
        f'<div class="phase-indicator">회상 단계 | 기억나는 단어를 입력하세요</div>',
        unsafe_allow_html=True
    )

    # 시간 제한 없음
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
    """회상 완료 처리"""
    session = st.session_state.session

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
            response_time=0,  # 개별 측정 미구현
            is_correct=is_correct,
            is_intrusion=is_intrusion,
            original_position=original_position
        )
        session.recalled_words.append(response)

    session.end_time = datetime.now().isoformat()
    st.session_state.phase = 'results'


def show_results():
    """결과 표시"""
    session = st.session_state.session
    scores = calculate_recall_scores(session)

    st.markdown("## 실험 완료!")
    st.balloons()

    st.markdown("### 결과 요약")

    # 주요 지표
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "정확 회상",
            f"{scores['correct_recalls']} / {scores['total_presented']}",
            f"{scores['recall_rate']*100:.1f}%"
        )

    with col2:
        st.metric(
            "회상률",
            f"{scores['recall_rate']*100:.1f}%"
        )

    with col3:
        st.metric(
            "침입 오류",
            scores['intrusion_errors']
        )

    st.markdown("---")

    # 범주별 회상률
    st.markdown("### 범주별 회상률")

    col1, col2, col3 = st.columns(3)

    with col1:
        pos_rate = scores['category_rate']['positive'] * 100
        st.metric(
            "긍정 단어",
            f"{scores['category_recall']['positive']} / {scores['category_total']['positive']}",
            f"{pos_rate:.1f}%" if scores['category_total']['positive'] > 0 else "-"
        )

    with col2:
        neg_rate = scores['category_rate']['negative'] * 100
        st.metric(
            "부정 단어",
            f"{scores['category_recall']['negative']} / {scores['category_total']['negative']}",
            f"{neg_rate:.1f}%" if scores['category_total']['negative'] > 0 else "-"
        )

    with col3:
        neu_rate = scores['category_rate']['neutral'] * 100
        st.metric(
            "중립 단어",
            f"{scores['category_recall']['neutral']} / {scores['category_total']['neutral']}",
            f"{neu_rate:.1f}%" if scores['category_total']['neutral'] > 0 else "-"
        )

    st.markdown("---")

    # 계열위치 효과
    st.markdown("### 계열위치 효과")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("초두 효과 (처음)", scores['serial_position']['primacy'])

    with col2:
        st.metric("중간", scores['serial_position']['middle'])

    with col3:
        st.metric("최신 효과 (마지막)", scores['serial_position']['recency'])

    st.markdown("---")

    # 방해과제 결과
    if session.distractor_total > 0:
        st.markdown("### 방해과제 (산수)")
        st.metric(
            "정확도",
            f"{session.distractor_correct} / {session.distractor_total}",
            f"{scores['distractor_accuracy']*100:.1f}%"
        )

    st.markdown("---")

    # 상세 결과
    with st.expander("제시된 단어 목록"):
        for w in session.presented_words:
            recalled = "✓" if any(r.recalled_word == w.word for r in session.recalled_words if r.is_correct) else ""
            st.markdown(f"{w.presentation_order}. **{w.word}** ({w.category}) {recalled}")

    with st.expander("회상된 단어"):
        for r in session.recalled_words:
            if r.is_correct:
                st.markdown(f'<span class="recalled-word correct-word">{r.recalled_word}</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="recalled-word intrusion-word">{r.recalled_word} (침입오류)</span>', unsafe_allow_html=True)

    st.markdown("---")

    # 데이터 다운로드
    st.markdown("### 데이터 저장")

    col1, col2 = st.columns(2)

    with col1:
        json_data = session.to_json()
        st.download_button(
            label="JSON으로 다운로드",
            data=json_data,
            file_name=f"free_recall_{session.session_id}.json",
            mime="application/json"
        )

    with col2:
        spreadsheet_data = prepare_for_spreadsheet(session)
        csv_content = "\n".join([",".join(map(str, row)) for row in spreadsheet_data])
        st.download_button(
            label="CSV로 다운로드",
            data=csv_content,
            file_name=f"free_recall_{session.session_id}.csv",
            mime="text/csv"
        )

    st.markdown("---")

    # 새 실험
    if st.button("새 실험 시작", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def reset_experiment():
    """실험 초기화"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def main():
    """메인 함수"""
    init_session_state()

    phase = st.session_state.phase

    # 화면 전환 시 기존 UI가 "아래에 남는" 현상을 막기 위해,
    # 메인/사이드바 모두 placeholder를 고정된 위치에 먼저 만들고
    # phase에 따라 한 쪽을 비우는 방식으로 렌더링한다.
    sidebar_area = st.sidebar.empty()
    setup_area = st.empty()
    task_area = st.empty()

    with sidebar_area.container():
        if phase not in ['setup', 'results']:
            if st.button("🛑 Stop", use_container_width=True):
                reset_experiment()
                st.rerun()

    if phase == 'setup':
        task_area.empty()
        with setup_area.container():
            show_setup()
    else:
        setup_area.empty()
        with task_area.container():
            if phase == 'encoding':
                show_encoding()
            elif phase == 'distractor':
                show_distractor()
            elif phase == 'recall':
                show_recall()
            elif phase == 'results':
                show_results()


if __name__ == "__main__":
    main()
