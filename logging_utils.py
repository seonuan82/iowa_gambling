"""
Logging Utilities for Psychology Experiments
심리학 실험 데이터 로깅 유틸리티

Google Spreadsheet 또는 로컬 파일 로깅 지원
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import csv


# 로컬 로깅 디렉토리
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")


def ensure_log_dir():
    """로그 디렉토리 생성"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)


def get_log_file_path(task_name: str, date: Optional[str] = None) -> str:
    """로그 파일 경로 생성"""
    ensure_log_dir()
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    return os.path.join(LOG_DIR, f"{task_name}_{date}.csv")


# ============================================================
# Iowa Gambling Task 로깅 함수
# ============================================================

def log_session_start(session_id: str, participant_id: str):
    """IGT 세션 시작 로깅"""
    log_file = get_log_file_path("igt_sessions")

    # 파일이 없으면 헤더 추가
    write_header = not os.path.exists(log_file)

    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "timestamp", "session_id", "participant_id", "event", "details"
            ])
        writer.writerow([
            datetime.now().isoformat(),
            session_id,
            participant_id,
            "session_start",
            ""
        ])


def log_trial(
    session_id: str,
    participant_id: str,
    trial_number: int,
    deck_choice: str,
    reward: int,
    penalty: int,
    net_outcome: int,
    balance: int
):
    """IGT 시행 로깅"""
    log_file = get_log_file_path("igt_trials")

    write_header = not os.path.exists(log_file)

    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "timestamp", "session_id", "participant_id",
                "trial_number", "deck_choice", "reward", "penalty",
                "net_outcome", "balance"
            ])
        writer.writerow([
            datetime.now().isoformat(),
            session_id,
            participant_id,
            trial_number,
            deck_choice,
            reward,
            penalty,
            net_outcome,
            balance
        ])


def log_session_end(
    session_id: str,
    participant_id: str,
    final_balance: int,
    net_score: int,
    deck_counts: Dict[str, int]
):
    """IGT 세션 종료 로깅"""
    log_file = get_log_file_path("igt_sessions")

    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            session_id,
            participant_id,
            "session_end",
            json.dumps({
                "final_balance": final_balance,
                "net_score": net_score,
                "deck_counts": deck_counts
            }, ensure_ascii=False)
        ])


# ============================================================
# Free Recall Task 로깅 함수
# ============================================================

def log_free_recall_session_start(
    session_id: str,
    participant_id: str,
    condition: str,
    processing_type: str,
    num_words: int
):
    """Free Recall 세션 시작 로깅"""
    log_file = get_log_file_path("free_recall_sessions")

    write_header = not os.path.exists(log_file)

    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "timestamp", "session_id", "participant_id",
                "condition", "processing_type", "num_words",
                "event", "details"
            ])
        writer.writerow([
            datetime.now().isoformat(),
            session_id,
            participant_id,
            condition,
            processing_type,
            num_words,
            "session_start",
            ""
        ])


def log_word_presentation(
    session_id: str,
    participant_id: str,
    word: str,
    position: int,
    category: str,
    valence: float,
    arousal: float
):
    """단어 제시 로깅"""
    log_file = get_log_file_path("free_recall_presentations")

    write_header = not os.path.exists(log_file)

    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "timestamp", "session_id", "participant_id",
                "word", "position", "category", "valence", "arousal"
            ])
        writer.writerow([
            datetime.now().isoformat(),
            session_id,
            participant_id,
            word,
            position,
            category,
            valence,
            arousal
        ])


def log_recall_response(
    session_id: str,
    participant_id: str,
    recalled_word: str,
    recall_order: int,
    is_correct: bool,
    is_intrusion: bool,
    original_position: Optional[int]
):
    """회상 응답 로깅"""
    log_file = get_log_file_path("free_recall_responses")

    write_header = not os.path.exists(log_file)

    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "timestamp", "session_id", "participant_id",
                "recalled_word", "recall_order", "is_correct",
                "is_intrusion", "original_position"
            ])
        writer.writerow([
            datetime.now().isoformat(),
            session_id,
            participant_id,
            recalled_word,
            recall_order,
            is_correct,
            is_intrusion,
            original_position if original_position else ""
        ])


def log_free_recall_session_end(
    session_id: str,
    participant_id: str,
    total_presented: int,
    correct_recalls: int,
    recall_rate: float,
    intrusion_errors: int,
    category_recall: Dict[str, int],
    serial_position: Dict[str, int],
    distractor_accuracy: float
):
    """Free Recall 세션 종료 로깅"""
    log_file = get_log_file_path("free_recall_sessions")

    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            session_id,
            participant_id,
            "",  # condition
            "",  # processing_type
            "",  # num_words
            "session_end",
            json.dumps({
                "total_presented": total_presented,
                "correct_recalls": correct_recalls,
                "recall_rate": recall_rate,
                "intrusion_errors": intrusion_errors,
                "category_recall": category_recall,
                "serial_position": serial_position,
                "distractor_accuracy": distractor_accuracy
            }, ensure_ascii=False)
        ])


# ============================================================
# 범용 로깅 함수
# ============================================================

def log_event(
    task_name: str,
    session_id: str,
    participant_id: str,
    event_type: str,
    data: Dict[str, Any]
):
    """범용 이벤트 로깅"""
    log_file = get_log_file_path(f"{task_name}_events")

    write_header = not os.path.exists(log_file)

    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "timestamp", "session_id", "participant_id",
                "event_type", "data"
            ])
        writer.writerow([
            datetime.now().isoformat(),
            session_id,
            participant_id,
            event_type,
            json.dumps(data, ensure_ascii=False)
        ])


def export_session_data(task_name: str, session_id: str) -> Dict[str, List]:
    """특정 세션의 모든 데이터 내보내기"""
    data = {}

    # 관련 로그 파일들 찾기
    ensure_log_dir()
    for filename in os.listdir(LOG_DIR):
        if filename.startswith(task_name) and filename.endswith('.csv'):
            filepath = os.path.join(LOG_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = [row for row in reader if row.get('session_id') == session_id]
                if rows:
                    data[filename] = rows

    return data
