"""
Free Recall Task Utilities
단어목록 자유회상 과제를 위한 유틸리티 모듈

홍영지 등(2016)의 한국어 정서단어 목록을 기반으로 구성
"""

import random
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
import uuid


# 한국어 정서단어 목록 (홍영지 등, 2016 기반)
# 정서가: 1(매우 부정) ~ 9(매우 긍정), 각성가: 1(안정) ~ 9(흥분), 구체성: 1(추상) ~ 9(구체)
WORD_DATABASE = {
    # 긍정 단어 (정서가 6점 이상)
    "positive": [
        {"word": "기쁨", "valence": 8.24, "arousal": 5.82, "concreteness": 2.87},
        {"word": "사랑", "valence": 8.17, "arousal": 4.54, "concreteness": 2.97},
        {"word": "우정", "valence": 8.03, "arousal": 3.41, "concreteness": 2.85},
        {"word": "행운", "valence": 7.74, "arousal": 3.83, "concreteness": 2.61},
        {"word": "희망", "valence": 7.28, "arousal": 5.33, "concreteness": 2.45},
        {"word": "성공", "valence": 7.51, "arousal": 5.42, "concreteness": 2.94},
        {"word": "평화", "valence": 7.86, "arousal": 2.52, "concreteness": 2.89},
        {"word": "감사", "valence": 7.96, "arousal": 3.36, "concreteness": 3.13},
        {"word": "자유", "valence": 7.82, "arousal": 3.85, "concreteness": 2.76},
        {"word": "축하", "valence": 7.73, "arousal": 4.58, "concreteness": 3.76},
        {"word": "승리", "valence": 7.55, "arousal": 6.83, "concreteness": 3.73},
        {"word": "건강", "valence": 7.08, "arousal": 3.13, "concreteness": 3.66},
        {"word": "휴식", "valence": 7.80, "arousal": 2.01, "concreteness": 3.38},
        {"word": "친구", "valence": 7.88, "arousal": 3.24, "concreteness": 6.08},
        {"word": "선물", "valence": 7.23, "arousal": 5.30, "concreteness": 7.04},
        {"word": "여행", "valence": 7.66, "arousal": 6.10, "concreteness": 5.03},
        {"word": "보석", "valence": 6.73, "arousal": 4.42, "concreteness": 7.91},
        {"word": "노래", "valence": 7.32, "arousal": 4.21, "concreteness": 6.08},
        {"word": "낭만", "valence": 7.40, "arousal": 4.16, "concreteness": 2.34},
        {"word": "매력", "valence": 7.50, "arousal": 5.28, "concreteness": 2.66},
    ],
    # 부정 단어 (정서가 4점 이하)
    "negative": [
        {"word": "고통", "valence": 2.42, "arousal": 6.83, "concreteness": 3.42},
        {"word": "슬픔", "valence": 2.81, "arousal": 5.46, "concreteness": 4.18},
        {"word": "분노", "valence": 2.84, "arousal": 6.61, "concreteness": 3.25},
        {"word": "공포", "valence": 2.84, "arousal": 7.19, "concreteness": 2.98},
        {"word": "불안", "valence": 2.87, "arousal": 6.48, "concreteness": 2.73},
        {"word": "절망", "valence": 2.11, "arousal": 6.21, "concreteness": 2.73},
        {"word": "증오", "valence": 1.72, "arousal": 7.12, "concreteness": 2.92},
        {"word": "후회", "valence": 2.93, "arousal": 5.23, "concreteness": 2.87},
        {"word": "실패", "valence": 2.76, "arousal": 6.67, "concreteness": 2.67},
        {"word": "이별", "valence": 2.58, "arousal": 6.23, "concreteness": 3.73},
        {"word": "가난", "valence": 2.91, "arousal": 5.87, "concreteness": 3.35},
        {"word": "전쟁", "valence": 2.24, "arousal": 7.43, "concreteness": 5.90},
        {"word": "폭력", "valence": 2.24, "arousal": 7.24, "concreteness": 4.78},
        {"word": "죽음", "valence": 2.36, "arousal": 5.13, "concreteness": 4.72},
        {"word": "상처", "valence": 2.85, "arousal": 6.02, "concreteness": 6.15},
        {"word": "위험", "valence": 2.97, "arousal": 6.76, "concreteness": 3.33},
        {"word": "걱정", "valence": 3.36, "arousal": 5.63, "concreteness": 2.86},
        {"word": "외로움", "valence": 3.41, "arousal": 4.46, "concreteness": 2.62},
        {"word": "긴장", "valence": 4.10, "arousal": 6.96, "concreteness": 3.07},
        {"word": "피해", "valence": 2.66, "arousal": 6.21, "concreteness": 3.77},
    ],
    # 중립 단어 (정서가 4~6점, 사물 명사)
    "neutral": [
        {"word": "책상", "valence": 5.55, "arousal": 3.80, "concreteness": 8.61},
        {"word": "의자", "valence": 5.46, "arousal": 3.55, "concreteness": 8.30},
        {"word": "창문", "valence": 5.45, "arousal": 4.09, "concreteness": 8.50},
        {"word": "시계", "valence": 5.62, "arousal": 3.87, "concreteness": 8.53},
        {"word": "거울", "valence": 5.45, "arousal": 4.09, "concreteness": 8.50},
        {"word": "우산", "valence": 5.10, "arousal": 3.70, "concreteness": 8.66},
        {"word": "신문", "valence": 5.69, "arousal": 3.95, "concreteness": 8.55},
        {"word": "바위", "valence": 5.22, "arousal": 3.78, "concreteness": 8.60},
        {"word": "단추", "valence": 5.19, "arousal": 3.93, "concreteness": 8.53},
        {"word": "열쇠", "valence": 5.74, "arousal": 4.00, "concreteness": 8.59},
        {"word": "그릇", "valence": 5.41, "arousal": 3.85, "concreteness": 8.42},
        {"word": "모자", "valence": 5.51, "arousal": 4.18, "concreteness": 8.55},
        {"word": "가구", "valence": 5.17, "arousal": 3.85, "concreteness": 8.18},
        {"word": "건물", "valence": 5.30, "arousal": 3.88, "concreteness": 8.27},
        {"word": "도구", "valence": 5.56, "arousal": 4.38, "concreteness": 7.28},
        {"word": "글자", "valence": 5.29, "arousal": 3.58, "concreteness": 7.43},
        {"word": "탁자", "valence": 4.96, "arousal": 3.91, "concreteness": 8.51},
        {"word": "볼펜", "valence": 5.15, "arousal": 4.01, "concreteness": 8.69},
        {"word": "냉장고", "valence": 5.43, "arousal": 4.89, "concreteness": 8.71},
        {"word": "전화선", "valence": 5.68, "arousal": 4.04, "concreteness": 8.55},
    ]
}


def generate_session_id() -> str:
    """고유한 세션 ID 생성"""
    return f"FR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


@dataclass
class WordStimulus:
    """단어 자극 정보"""
    word: str
    valence: float
    arousal: float
    concreteness: float
    category: str  # positive, negative, neutral
    presentation_order: int = 0


@dataclass
class RecallResponse:
    """회상 응답 기록"""
    recalled_word: str
    recall_order: int
    response_time: float  # 입력까지 걸린 시간 (초)
    is_correct: bool  # 제시된 단어 목록에 있는지
    is_intrusion: bool  # 침입 오류 (제시되지 않은 단어)
    original_position: Optional[int] = None  # 원래 제시 순서


@dataclass
class FreeRecallSession:
    """자유회상 과제 세션"""
    session_id: str
    participant_id: str
    condition: str  # emotional, neutral, mixed
    processing_type: str  # semantic (의미판단), perceptual (외형판단)
    start_time: str
    end_time: Optional[str] = None

    # 실험 파라미터
    num_words: int = 15
    presentation_duration: float = 2.0  # 단어당 제시 시간 (초)
    distractor_duration: int = 30  # 방해과제 시간 (초)
    recall_duration: int = 90  # 회상 시간 (초)

    # 제시된 단어 목록
    presented_words: List[WordStimulus] = field(default_factory=list)

    # 회상 응답
    recalled_words: List[RecallResponse] = field(default_factory=list)

    # 방해과제 결과
    distractor_correct: int = 0
    distractor_total: int = 0

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "condition": self.condition,
            "processing_type": self.processing_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "num_words": self.num_words,
            "presentation_duration": self.presentation_duration,
            "distractor_duration": self.distractor_duration,
            "recall_duration": self.recall_duration,
            "presented_words": [asdict(w) for w in self.presented_words],
            "recalled_words": [asdict(r) for r in self.recalled_words],
            "distractor_correct": self.distractor_correct,
            "distractor_total": self.distractor_total
        }

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class WordListManager:
    """단어 목록 관리 클래스"""

    def __init__(self):
        self.word_db = WORD_DATABASE

    def create_word_list(
        self,
        condition: str = "mixed",
        num_words: int = 15,
        match_arousal: bool = True
    ) -> List[WordStimulus]:
        """
        실험 조건에 맞는 단어 목록 생성

        Args:
            condition: "emotional" (정서단어만), "neutral" (중립단어만), "mixed" (혼합)
            num_words: 단어 개수
            match_arousal: 각성가 매칭 여부
        """
        words = []

        if condition == "emotional":
            # 긍정/부정 단어 동일 비율
            n_each = num_words // 2
            pos_words = random.sample(self.word_db["positive"], min(n_each, len(self.word_db["positive"])))
            neg_words = random.sample(self.word_db["negative"], min(num_words - n_each, len(self.word_db["negative"])))

            for w in pos_words:
                words.append(WordStimulus(
                    word=w["word"],
                    valence=w["valence"],
                    arousal=w["arousal"],
                    concreteness=w["concreteness"],
                    category="positive"
                ))
            for w in neg_words:
                words.append(WordStimulus(
                    word=w["word"],
                    valence=w["valence"],
                    arousal=w["arousal"],
                    concreteness=w["concreteness"],
                    category="negative"
                ))

        elif condition == "neutral":
            neutral_words = random.sample(self.word_db["neutral"], min(num_words, len(self.word_db["neutral"])))
            for w in neutral_words:
                words.append(WordStimulus(
                    word=w["word"],
                    valence=w["valence"],
                    arousal=w["arousal"],
                    concreteness=w["concreteness"],
                    category="neutral"
                ))

        else:  # mixed
            # 긍정, 부정, 중립 각 1/3씩
            n_each = num_words // 3
            remainder = num_words % 3

            pos_words = random.sample(self.word_db["positive"], min(n_each, len(self.word_db["positive"])))
            neg_words = random.sample(self.word_db["negative"], min(n_each, len(self.word_db["negative"])))
            neu_words = random.sample(self.word_db["neutral"], min(n_each + remainder, len(self.word_db["neutral"])))

            for w in pos_words:
                words.append(WordStimulus(
                    word=w["word"],
                    valence=w["valence"],
                    arousal=w["arousal"],
                    concreteness=w["concreteness"],
                    category="positive"
                ))
            for w in neg_words:
                words.append(WordStimulus(
                    word=w["word"],
                    valence=w["valence"],
                    arousal=w["arousal"],
                    concreteness=w["concreteness"],
                    category="negative"
                ))
            for w in neu_words:
                words.append(WordStimulus(
                    word=w["word"],
                    valence=w["valence"],
                    arousal=w["arousal"],
                    concreteness=w["concreteness"],
                    category="neutral"
                ))

        # 무선화
        random.shuffle(words)

        # 제시 순서 부여
        for i, w in enumerate(words):
            w.presentation_order = i + 1

        return words


def calculate_recall_scores(session: FreeRecallSession) -> Dict:
    """회상 점수 계산"""
    presented_words = {w.word for w in session.presented_words}

    # 정확 회상 수
    correct_recalls = [r for r in session.recalled_words if r.is_correct]

    # 침입 오류 수
    intrusions = [r for r in session.recalled_words if r.is_intrusion]

    # 범주별 회상률
    category_recall = {"positive": 0, "negative": 0, "neutral": 0}
    category_total = {"positive": 0, "negative": 0, "neutral": 0}

    for w in session.presented_words:
        category_total[w.category] += 1

    for r in correct_recalls:
        # 회상된 단어의 범주 찾기
        for w in session.presented_words:
            if w.word == r.recalled_word:
                category_recall[w.category] += 1
                break

    # 계열위치 효과 분석
    serial_positions = {"primacy": 0, "middle": 0, "recency": 0}
    n_words = len(session.presented_words)
    primacy_range = min(3, n_words // 3)  # 처음 3개 또는 1/3
    recency_range = min(3, n_words // 3)  # 마지막 3개 또는 1/3

    for r in correct_recalls:
        if r.original_position:
            if r.original_position <= primacy_range:
                serial_positions["primacy"] += 1
            elif r.original_position > n_words - recency_range:
                serial_positions["recency"] += 1
            else:
                serial_positions["middle"] += 1

    return {
        "total_presented": len(session.presented_words),
        "total_recalled": len(session.recalled_words),
        "correct_recalls": len(correct_recalls),
        "recall_rate": len(correct_recalls) / len(session.presented_words) if session.presented_words else 0,
        "intrusion_errors": len(intrusions),
        "category_recall": category_recall,
        "category_total": category_total,
        "category_rate": {
            k: category_recall[k] / category_total[k] if category_total[k] > 0 else 0
            for k in category_recall
        },
        "serial_position": serial_positions,
        "distractor_accuracy": session.distractor_correct / session.distractor_total if session.distractor_total > 0 else 0
    }


def prepare_for_spreadsheet(session: FreeRecallSession) -> List[List]:
    """스프레드시트용 데이터 준비"""
    scores = calculate_recall_scores(session)

    # 헤더
    headers = [
        "session_id", "participant_id", "condition", "processing_type",
        "start_time", "end_time",
        "total_presented", "correct_recalls", "recall_rate",
        "intrusion_errors",
        "positive_recall", "negative_recall", "neutral_recall",
        "primacy", "middle", "recency",
        "distractor_accuracy"
    ]

    # 데이터 행
    data = [
        session.session_id,
        session.participant_id,
        session.condition,
        session.processing_type,
        session.start_time,
        session.end_time,
        scores["total_presented"],
        scores["correct_recalls"],
        f"{scores['recall_rate']:.3f}",
        scores["intrusion_errors"],
        scores["category_recall"]["positive"],
        scores["category_recall"]["negative"],
        scores["category_recall"]["neutral"],
        scores["serial_position"]["primacy"],
        scores["serial_position"]["middle"],
        scores["serial_position"]["recency"],
        f"{scores['distractor_accuracy']:.3f}"
    ]

    return [headers, data]


# 방해과제용 산수 문제 생성
def generate_math_problem() -> tuple:
    """간단한 산수 문제 생성 (덧셈/뺄셈)"""
    a = random.randint(10, 99)
    b = random.randint(1, 50)

    if random.choice([True, False]):
        # 덧셈
        answer = a + b
        problem = f"{a} + {b} = ?"
    else:
        # 뺄셈 (음수 방지)
        if a < b:
            a, b = b, a
        answer = a - b
        problem = f"{a} - {b} = ?"

    return problem, answer
