"""
Iowa Gambling Task - Utility Functions
로그 기록 및 데이터 관리를 위한 유틸리티
"""

import random
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json


@dataclass
class TrialResult:
    """단일 시행 결과"""
    trial_number: int
    deck_choice: str  # A, B, C, D
    reward: int
    penalty: int
    net_outcome: int
    balance_after: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GameSession:
    """게임 세션 데이터"""
    session_id: str
    participant_id: str
    start_time: str
    trials: List[TrialResult] = field(default_factory=list)
    initial_balance: int = 2000
    current_balance: int = 2000
    total_trials: int = 10
    end_time: Optional[str] = None

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "initial_balance": self.initial_balance,
            "final_balance": self.current_balance,
            "total_trials_completed": len(self.trials),
            "trials": [
                {
                    "trial": t.trial_number,
                    "deck": t.deck_choice,
                    "reward": t.reward,
                    "penalty": t.penalty,
                    "net": t.net_outcome,
                    "balance": t.balance_after,
                    "time": t.timestamp
                }
                for t in self.trials
            ]
        }

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class DeckManager:
    """
    Iowa Gambling Task 덱 관리

    덱 특성 (Bechara et al., 1994 기반 - 40장 고정 스케줄):
    - Deck A: 보상 $100, 10장 중 5장에서 손실, 불규칙 위치 (불리한 덱)
    - Deck B: 보상 $100, 10장 중 1장에서 큰 손실 (불리한 덱)
    - Deck C: 보상 $50, 10장 중 5장에서 작은 손실, 불규칙 위치 (유리한 덱)
    - Deck D: 보상 $50, 10장 중 1장에서 중간 손실 (유리한 덱)

    각 덱은 40장 단위로 순환하며, 10장당 기대값:
    - Deck A/B: -$250 (불리)
    - Deck C/D: +$250 (유리)
    """

    def __init__(self):
        # 보상 설정
        self.rewards = {
            'A': 100,
            'B': 100,
            'C': 50,
            'D': 50
        }

        # 40장 고정 스케줄 (Bechara et al., 1994 Figure 1 기반)
        # 손실 위치가 불규칙하게 배치됨
        self.penalty_schedules = {
            # Deck A: 10장당 5회 손실, 합계 $1250 (빈번하고 다양한 손실)
            'A': [
                0, 0, 150, 0, 300, 0, 200, 0, 250, 350,      # 1-10: 손실 5회, 합계 $1250
                0, 350, 0, 250, 0, 200, 0, 300, 150, 0,      # 11-20: 손실 5회, 합계 $1250
                150, 0, 300, 0, 0, 200, 250, 0, 0, 350,      # 21-30: 손실 5회, 합계 $1250
                350, 0, 200, 250, 0, 0, 150, 0, 300, 0,      # 31-40: 손실 5회, 합계 $1250
            ],
            # Deck B: 10장당 1회 큰 손실 $1250 (드물지만 치명적)
            'B': [
                0, 0, 0, 0, 0, 0, 0, 0, 1250, 0,             # 1-10: 9번째에서 $1250
                0, 0, 0, 0, 0, 0, 0, 0, 0, 1250,             # 11-20: 10번째에서 $1250
                0, 0, 0, 0, 1250, 0, 0, 0, 0, 0,             # 21-30: 5번째에서 $1250
                0, 0, 0, 0, 0, 0, 1250, 0, 0, 0,             # 31-40: 7번째에서 $1250
            ],
            # Deck C: 10장당 5회 손실, 합계 $250 (빈번하지만 작은 손실)
            'C': [
                0, 0, 50, 0, 50, 0, 50, 0, 50, 50,           # 1-10: 손실 5회, 합계 $250
                0, 25, 0, 75, 0, 50, 0, 25, 75, 0,           # 11-20: 손실 5회, 합계 $250
                50, 0, 25, 0, 0, 75, 50, 0, 0, 50,           # 21-30: 손실 5회, 합계 $250
                25, 0, 75, 50, 0, 0, 25, 0, 75, 0,           # 31-40: 손실 5회, 합계 $250
            ],
            # Deck D: 10장당 1회 손실 $250 (드물고 중간 크기)
            'D': [
                0, 0, 0, 0, 0, 0, 0, 0, 250, 0,              # 1-10: 9번째에서 $250
                0, 0, 0, 0, 0, 0, 0, 0, 0, 250,              # 11-20: 10번째에서 $250
                0, 0, 0, 0, 250, 0, 0, 0, 0, 0,              # 21-30: 5번째에서 $250
                0, 0, 0, 0, 0, 0, 250, 0, 0, 0,              # 31-40: 7번째에서 $250
            ],
        }

        # 각 덱별 현재 카드 인덱스 (0-39 순환)
        self.deck_indices = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

        # 각 덱별 선택 횟수 추적
        self.deck_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

    def draw_card(self, deck: str) -> tuple:
        """
        덱에서 카드를 뽑고 보상/손실 반환 (고정 스케줄 방식)

        Returns:
            (reward, penalty, net_outcome)
        """
        if deck not in self.rewards:
            raise ValueError(f"Invalid deck: {deck}")

        self.deck_counts[deck] += 1

        reward = self.rewards[deck]

        # 현재 인덱스의 손실 가져오기
        current_index = self.deck_indices[deck]
        penalty = self.penalty_schedules[deck][current_index]

        # 인덱스 증가 (40장 단위 순환)
        self.deck_indices[deck] = (current_index + 1) % 40

        net_outcome = reward - penalty

        return reward, penalty, net_outcome

    def get_deck_counts(self) -> Dict[str, int]:
        """각 덱별 선택 횟수 반환"""
        return self.deck_counts.copy()

    def reset(self):
        """덱 카운트 초기화"""
        self.deck_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}


def generate_session_id() -> str:
    """고유 세션 ID 생성"""
    return datetime.now().strftime("%Y%m%d_%H%M%S_") + str(random.randint(1000, 9999))


def calculate_igt_score(session: GameSession) -> Dict:
    """
    IGT 점수 계산

    Returns:
        - net_score: (C+D) - (A+B) 점수
        - deck_counts: 각 덱 선택 횟수
        - advantageous_ratio: 유리한 덱 선택 비율
    """
    deck_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

    for trial in session.trials:
        deck_counts[trial.deck_choice] += 1

    # Net Score: (유리한 덱) - (불리한 덱)
    advantageous = deck_counts['C'] + deck_counts['D']
    disadvantageous = deck_counts['A'] + deck_counts['B']
    net_score = advantageous - disadvantageous

    total = len(session.trials)
    advantageous_ratio = advantageous / total if total > 0 else 0

    return {
        'net_score': net_score,
        'deck_counts': deck_counts,
        'advantageous_ratio': advantageous_ratio,
        'total_trials': total,
        'final_balance': session.current_balance,
        'profit': session.current_balance - session.initial_balance
    }


def format_trial_log(trial: TrialResult) -> str:
    """시행 결과를 로그 문자열로 포맷"""
    return (
        f"Trial {trial.trial_number:3d} | "
        f"Deck {trial.deck_choice} | "
        f"Reward: ${trial.reward:4d} | "
        f"Penalty: ${trial.penalty:4d} | "
        f"Net: ${trial.net_outcome:+5d} | "
        f"Balance: ${trial.balance_after:5d}"
    )


def prepare_for_spreadsheet(session: GameSession) -> List[List]:
    """
    Google Spreadsheet 업로드용 데이터 준비

    Returns:
        2D 리스트 (행 단위 데이터)
    """
    rows = []

    # 헤더
    header = [
        "session_id", "participant_id", "trial", "deck",
        "reward", "penalty", "net_outcome", "balance", "timestamp"
    ]
    rows.append(header)

    # 데이터 행
    for trial in session.trials:
        row = [
            session.session_id,
            session.participant_id,
            trial.trial_number,
            trial.deck_choice,
            trial.reward,
            trial.penalty,
            trial.net_outcome,
            trial.balance_after,
            trial.timestamp
        ]
        rows.append(row)

    return rows
