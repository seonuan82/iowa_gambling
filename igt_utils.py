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

    덱 특성 (Bechara et al., 1994 기반):
    - Deck A: 보상 $100, 손실 빈번하고 큼 (불리한 덱)
    - Deck B: 보상 $100, 손실 드물지만 매우 큼 (불리한 덱)
    - Deck C: 보상 $50, 손실 빈번하지만 작음 (유리한 덱)
    - Deck D: 보상 $50, 손실 드물고 작음 (유리한 덱)
    """

    def __init__(self):
        self.deck_configs = {
            'A': {
                'reward': 100,
                'penalty_prob': 0.5,  # 50% 확률로 손실
                'penalties': [150, 200, 250, 300, 350],  # 가능한 손실 금액
                'description': 'Deck A'
            },
            'B': {
                'reward': 100,
                'penalty_prob': 0.1,  # 10% 확률로 손실
                'penalties': [1250],  # 큰 손실
                'description': 'Deck B'
            },
            'C': {
                'reward': 50,
                'penalty_prob': 0.5,  # 50% 확률로 손실
                'penalties': [25, 50, 75],  # 작은 손실
                'description': 'Deck C'
            },
            'D': {
                'reward': 50,
                'penalty_prob': 0.1,  # 10% 확률로 손실
                'penalties': [250],  # 중간 손실
                'description': 'Deck D'
            }
        }

        # 각 덱별 선택 횟수 추적
        self.deck_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

    def draw_card(self, deck: str) -> tuple:
        """
        덱에서 카드를 뽑고 보상/손실 반환

        Returns:
            (reward, penalty, net_outcome)
        """
        if deck not in self.deck_configs:
            raise ValueError(f"Invalid deck: {deck}")

        config = self.deck_configs[deck]
        self.deck_counts[deck] += 1

        reward = config['reward']

        # 손실 발생 여부 결정
        if random.random() < config['penalty_prob']:
            penalty = random.choice(config['penalties'])
        else:
            penalty = 0

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
