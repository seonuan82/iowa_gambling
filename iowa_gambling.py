"""
Iowa Gambling Task (IGT)
Streamlit 기반 심리학 실험 과제

Bechara et al. (1994) 기반 의사결정 과제
"""

import streamlit as st
import time
from datetime import datetime
from igt_utils import (
    DeckManager,
    GameSession,
    TrialResult,
    generate_session_id,
    calculate_igt_score,
    prepare_for_spreadsheet
)
from igt_logging_utils import (
    log_batch_trials,
    log_session_start,
    log_session_end
)

# 배치 로깅 간격 (N시행마다 Google Sheets에 기록)
BATCH_LOG_INTERVAL = 100

# 페이지 설정
st.set_page_config(
    page_title="Iowa Gambling Task",
    page_icon="🎴",
    layout="centered"
)

# CSS 스타일
st.markdown("""
<style>
    .deck-button {
        font-size: 24px;
        padding: 20px;
        margin: 10px;
    }
    .balance-display {
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    .positive {
        color: #28a745;
    }
    .negative {
        color: #dc3545;
    }
    .neutral {
        color: #6c757d;
    }
    .result-box {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
    }
    .stButton > button {
        width: 100%;
        height: 120px;
        font-size: 32px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """세션 상태 초기화"""
    if 'game_started' not in st.session_state:
        st.session_state.game_started = False
    if 'game_ended' not in st.session_state:
        st.session_state.game_ended = False
    if 'session' not in st.session_state:
        st.session_state.session = None
    if 'deck_manager' not in st.session_state:
        st.session_state.deck_manager = None
    if 'last_result' not in st.session_state:
        st.session_state.last_result = None
    if 'show_result' not in st.session_state:
        st.session_state.show_result = False
    if 'show_participant_input' not in st.session_state:
        st.session_state.show_participant_input = False
    if 'logged_end' not in st.session_state:
        st.session_state.logged_end = False
    if 'game_start_timestamp' not in st.session_state:
        st.session_state.game_start_timestamp = None
    if 'last_logged_trial_idx' not in st.session_state:
        st.session_state.last_logged_trial_idx = 0
    if 'game_end_duration' not in st.session_state:
        st.session_state.game_end_duration = None


def show_instructions():
    """게임 설명 표시"""
    st.markdown("## 🎴 카드 선택 게임 안내")
    st.markdown("""
    이 과제에서는 4개의 카드 덱(A, B, C, D) 중에서 카드를 선택하게 됩니다.

    **규칙:**
    - 시작 금액: **$2,000**
    - 각 카드를 선택하면 **보상**을 받지만, 때로는 **손실**도 발생합니다.
    - 목표는 가능한 **많은 돈을 버는 것**입니다.
    - 실험자가 중단을 알릴 때까지 계속 진행합니다.

    **중요:**
    - 어떤 덱이 유리하고 불리한지는 직접 경험하며 파악해야 합니다.
    - 각 덱의 보상과 손실 패턴이 다릅니다.

    ---
    이 게임에서의 선택 패턴은  
    **다른 참가자들과 비교 분석**될 수 있습니다.

    당신은 어느 쪽일까요?
    """)

    if st.button("▶️ 시작하기"):
        st.session_state.show_participant_input = True

def show_participant_input():
    """참가자 ID 입력"""
    st.markdown("## 🧑 참가자 정보 입력")

    participant_id = st.text_input(
        "참가자 ID를 입력하세요",
        placeholder="예: P001"
    )

    if st.button("게임 시작"):
        if participant_id.strip() == "":
            st.warning("참가자 ID를 입력해주세요.")
        else:
            start_game(participant_id)


def start_game(participant_id: str):
    """게임 시작"""
    st.session_state.game_started = True
    st.session_state.game_ended = False
    st.session_state.deck_manager = DeckManager()
    st.session_state.session = GameSession(
        session_id=generate_session_id(),
        participant_id=participant_id,
        start_time=datetime.now().isoformat()
    )
    st.session_state.last_result = None
    st.session_state.show_result = False
    st.session_state.game_start_timestamp = time.time()
    st.session_state.last_logged_trial_idx = 0

    # Google Spreadsheet 로깅
    log_session_start(
        session_id=st.session_state.session.session_id,
        participant_id=participant_id
    )
    
    st.session_state.show_participant_input = False
    st.rerun()

def select_deck(deck: str):
    """덱 선택 처리"""
    session = st.session_state.session
    deck_manager = st.session_state.deck_manager

    # 카드 뽑기
    reward, penalty, net_outcome = deck_manager.draw_card(deck)

    # 잔액 업데이트
    session.current_balance += net_outcome

    # 시행 결과 기록
    trial = TrialResult(
        trial_number=len(session.trials) + 1,
        deck_choice=deck,
        reward=reward,
        penalty=penalty,
        net_outcome=net_outcome,
        balance_after=session.current_balance
    )
    session.trials.append(trial)

    # 주기적 배치 로깅 (N시행마다)
    if len(session.trials) % BATCH_LOG_INTERVAL == 0:
        batch_log_pending_trials()

    # 결과 저장
    st.session_state.last_result = trial
    st.session_state.show_result = True

    # 게임 종료 체크
    if len(session.trials) >= session.total_trials:
        session.end_time = datetime.now().isoformat()
        st.session_state.game_end_duration = time.time() - st.session_state.game_start_timestamp
        st.session_state.game_ended = True


def display_balance():
    """현재 잔액 표시"""
    session = st.session_state.session
    balance = session.current_balance
    initial = session.initial_balance

    if balance > initial:
        color_class = "positive"
        change = f"+${balance - initial}"
    elif balance < initial:
        color_class = "negative"
        change = f"-${initial - balance}"
    else:
        color_class = "neutral"
        change = "$0"

    st.markdown(f"""
    <div class="balance-display">
        현재 잔액: <span class="{color_class}">${balance:,}</span>
        <br><small>변화: {change}</small>
    </div>
    """, unsafe_allow_html=True)


def display_last_result():
    """마지막 결과 표시 (컴팩트 버전)"""
    if st.session_state.show_result and st.session_state.last_result:
        result = st.session_state.last_result

        # 양쪽에 빈 공간을 두어 중앙에 작게 표시
        _, col1, col2, _ = st.columns([1, 1, 1, 1])

        with col1:
            st.metric("보상", f"${result.reward}")

        with col2:
            if result.penalty > 0:
                st.metric("손실", f"-${result.penalty}")
            else:
                st.metric("손실", "$0")

        #with col3:
         #   if result.net_outcome >= 0:
          #      st.metric("순수익", f"+${result.net_outcome}")
           # else:
            #    st.metric("순수익", f"-${abs(result.net_outcome)}")


def display_decks():
    """4개 덱 버튼 표시"""
    st.markdown("### 카드 덱을 선택하세요")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("A", key="deck_a", use_container_width=True):
            select_deck('A')
            st.rerun()

    with col2:
        if st.button("B", key="deck_b", use_container_width=True):
            select_deck('B')
            st.rerun()

    with col3:
        if st.button("C", key="deck_c", use_container_width=True):
            select_deck('C')
            st.rerun()

    with col4:
        if st.button("D", key="deck_d", use_container_width=True):
            select_deck('D')
            st.rerun()


def display_progress():
    """진행 상황 표시 (시행 횟수는 참가자에게 숨김)"""
    session = st.session_state.session
    current = len(session.trials)

    st.markdown(f"**완료한 시행: {current}회**")


def batch_log_pending_trials():
    """미로깅 시행들을 배치로 Google Spreadsheet에 기록"""
    session = st.session_state.session
    last_idx = st.session_state.last_logged_trial_idx
    current_idx = len(session.trials)

    if current_idx <= last_idx:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trials_data = []
    for trial in session.trials[last_idx:current_idx]:
        trials_data.append([
            timestamp,
            session.session_id,
            session.participant_id,
            trial.trial_number,
            trial.deck_choice,
            trial.reward,
            trial.penalty,
            trial.net_outcome,
            trial.balance_after
        ])

    log_batch_trials(trials_data)
    st.session_state.last_logged_trial_idx = current_idx


def display_wait_screen(remaining_seconds):
    """최소 시간(10분) 미충족 시 대기 화면 표시"""
    minutes = int(remaining_seconds) // 60
    seconds = int(remaining_seconds) % 60

    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;
                min-height: 60vh; text-align: center;">
        <h2>잠시만 기다려 주세요</h2>
        <p style="font-size: 24px; color: #888;">다음 실험 준비 중입니다.</p>
        <p style="font-size: 20px; color: #666;">남은 시간: {minutes}분 {seconds:02d}초</p>
    </div>
    """, unsafe_allow_html=True)

    time.sleep(1)
    st.rerun()


def display_results():
    """최종 결과 표시"""
    session = st.session_state.session
    scores = calculate_igt_score(session)

    # 소요시간 (100번째 trial 클릭 시점 기준)
    duration_seconds = st.session_state.game_end_duration

    # 세션 종료 로깅 (한 번만 실행)
    if not st.session_state.logged_end:
        # 남은 시행 배치 로깅
        batch_log_pending_trials()
        log_session_end(
            session_id=session.session_id,
            participant_id=session.participant_id,
            final_balance=session.current_balance,
            net_score=scores['net_score'],
            deck_counts=scores['deck_counts'],
            duration_seconds=duration_seconds
        )
        st.session_state.logged_end = True

    st.markdown("## 게임 종료!")
    st.balloons()

    st.markdown("### 실험에 참가해 주셔서 감사합니다.")
    st.markdown("### 아래 버튼을 눌러 다음 실험으로 이동해 주세요.")
    
    #col1, col2 = st.columns(2)

    #with col1:
    #    st.metric("최종 잔액", f"${session.current_balance:,}")
    #    st.metric("총 수익/손실", f"${scores['profit']:+,}")

    #with col2:
    #    st.metric("IGT 점수 (C+D)-(A+B)", scores['net_score'])
    #    st.metric("유리한 덱 선택 비율", f"{scores['advantageous_ratio']:.1%}")

    #st.markdown("### 덱별 선택 횟수")
    #deck_counts = scores['deck_counts']

    #col1, col2, col3, col4 = st.columns(4)
    #with col1:
    #    st.metric("Deck A", deck_counts['A'])
    #with col2:
    #    st.metric("Deck B", deck_counts['B'])
    #with col3:
    #    st.metric("Deck C", deck_counts['C'])
    #with col4:
    #    st.metric("Deck D", deck_counts['D'])

    st.markdown("---")
    
    NEXT_EXPERIMENT_URL = "https://free-r-101.streamlit.app/"
    
    st.link_button(
        "▶ 다음 실험으로 이동",
        "https://free-r-101.streamlit.app/",
        use_container_width=True
    )

    # 데이터 다운로드 옵션
    #st.markdown("### 데이터 저장")

    # JSON 다운로드
    #json_data = session.to_json()
    #st.download_button(
    #    label="JSON으로 다운로드",
    #    data=json_data,
    #    file_name=f"igt_result_{session.participant_id}_{session.session_id}.json",
    #    mime="application/json"
    #)

    # CSV용 데이터 (Google Spreadsheet 업로드용)
    #spreadsheet_data = prepare_for_spreadsheet(session)
    #csv_content = "\n".join([",".join(map(str, row)) for row in spreadsheet_data])
    #st.download_button(
    #    label="CSV로 다운로드 (Spreadsheet용)",
    #    data=csv_content,
    #    file_name=f"igt_result_{session.participant_id}_{session.session_id}.csv",
    #    mime="text/csv"
    #)

    # 시행 기록 표시
    # with st.expander("전체 시행 기록 보기"):
    #    for trial in session.trials:
    #        net_color = "green" if trial.net_outcome >= 0 else "red"
    #        st.markdown(
    #            f"**Trial {trial.trial_number}** | "
    #            f"Deck {trial.deck_choice} | "
    #            f"보상: ${trial.reward} | "
    #            f"손실: ${trial.penalty} | "
    #            f"순수익: <span style='color:{net_color}'>${trial.net_outcome:+d}</span> | "
    #            f"잔액: ${trial.balance_after}",
    #            unsafe_allow_html=True
    #        )


def main():
    """메인 함수"""
    init_session_state()

    if not st.session_state.game_started:
        show_instructions()
    
        # 시작하기 버튼을 눌렀을 때만 참가자 ID 입력 표시
        if st.session_state.show_participant_input:
            st.markdown("---")
            show_participant_input()

    elif st.session_state.game_ended:
        # 게임 종료: 10분 미만이면 대기 화면, 이상이면 결과 표시
        MIN_GAME_DURATION = 600  # 10분 (초)
        elapsed = time.time() - st.session_state.game_start_timestamp

        if elapsed < MIN_GAME_DURATION:
            display_wait_screen(MIN_GAME_DURATION - elapsed)
        else:
            display_results()

    else:
        # 게임 진행 중
        display_balance()
        st.markdown("---")

        display_last_result()
        st.markdown("---")

        display_decks()


if __name__ == "__main__":
    main()

