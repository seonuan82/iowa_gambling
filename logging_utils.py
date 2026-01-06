"""
Iowa Gambling Task - Google Spreadsheet Logging
Google Spreadsheet 연동 로깅 유틸리티
"""

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
from typing import List, Optional

# Google Spreadsheet 정보 (메인 + 백업)
# TODO: 실제 사용 시 본인의 Spreadsheet URL로 변경
SHEET_INFO = [
    ("gsheet_b4", "https://docs.google.com/spreadsheets/d/1bA9yFiL7Y5Paxe5drC-t8Sc1V0Z7GT9vokBkU8wY6sI/edit?gid=0#gid=0"),   # backup 4
    ("gsheet_b5", "https://docs.google.com/spreadsheets/d/1Mj2KSoXtXbLziISgDUAkt9Mi6lB6NPr0A67GMLqsB48/edit?gid=0#gid=0"),   # backup 5
]


def init_sheet(secret_key_name: str, sheet_url: str):
    """
    Google Spreadsheet 초기화

    Args:
        secret_key_name: Streamlit secrets에 저장된 서비스 계정 키 이름
        sheet_url: Google Spreadsheet URL

    Returns:
        gspread worksheet 객체
    """
    scope = ["https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets[secret_key_name], scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url).sheet1
    return sheet


def log_event(text: str, user_id: str = "", event_type: str = "General"):
    """
    이벤트를 Google Spreadsheet에 기록

    Args:
        text: 로그 메시지
        user_id: 참가자 ID
        event_type: 이벤트 유형
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for idx, (secret_key, sheet_url) in enumerate(SHEET_INFO):
        try:
            sheet = init_sheet(secret_key, sheet_url)
            sheet.append_row([timestamp, user_id, event_type, text])
            break  # 성공 시 종료
        except Exception as e:
            if idx == len(SHEET_INFO) - 1:
                st.error(f"Failed to log even to backups. Error: {e}\n")
            else:
                time.sleep(1)


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
    """
    IGT 시행 결과를 Google Spreadsheet에 기록

    Args:
        session_id: 세션 ID
        participant_id: 참가자 ID
        trial_number: 시행 번호
        deck_choice: 선택한 덱 (A, B, C, D)
        reward: 보상 금액
        penalty: 손실 금액
        net_outcome: 순수익
        balance: 현재 잔액
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row_data = [
        timestamp,
        session_id,
        participant_id,
        trial_number,
        deck_choice,
        reward,
        penalty,
        net_outcome,
        balance
    ]

    for idx, (secret_key, sheet_url) in enumerate(SHEET_INFO):
        try:
            sheet = init_sheet(secret_key, sheet_url)
            sheet.append_row(row_data)
            break
        except Exception as e:
            if idx == len(SHEET_INFO) - 1:
                st.error(f"Failed to log trial. Error: {e}\n")
            else:
                time.sleep(1)


def log_session_start(session_id: str, participant_id: str):
    """세션 시작 로깅"""
    log_event(
        text=f"Session started - Initial balance: $2000",
        user_id=participant_id,
        event_type="SessionStart"
    )


def log_session_end(
    session_id: str,
    participant_id: str,
    final_balance: int,
    net_score: int,
    deck_counts: dict
):
    """
    세션 종료 로깅

    Args:
        session_id: 세션 ID
        participant_id: 참가자 ID
        final_balance: 최종 잔액
        net_score: IGT 점수 (C+D)-(A+B)
        deck_counts: 덱별 선택 횟수
    """
    summary = (
        f"Session ended - "
        f"Final: ${final_balance}, "
        f"Net Score: {net_score}, "
        f"A:{deck_counts['A']} B:{deck_counts['B']} "
        f"C:{deck_counts['C']} D:{deck_counts['D']}"
    )
    log_event(
        text=summary,
        user_id=participant_id,
        event_type="SessionEnd"
    )


def log_batch_trials(trials_data: List[List]):
    """
    여러 시행을 한 번에 기록 (게임 종료 시 사용)

    Args:
        trials_data: 2D 리스트 형태의 시행 데이터
    """
    for idx, (secret_key, sheet_url) in enumerate(SHEET_INFO):
        try:
            sheet = init_sheet(secret_key, sheet_url)
            # 헤더가 없으면 추가
            if sheet.row_count == 0 or not sheet.row_values(1):
                header = [
                    "timestamp", "session_id", "participant_id", "trial",
                    "deck", "reward", "penalty", "net_outcome", "balance"
                ]
                sheet.append_row(header)

            # 모든 시행 데이터 추가
            for row in trials_data:
                sheet.append_row(row)
            break
        except Exception as e:
            if idx == len(SHEET_INFO) - 1:
                st.error(f"Failed to log batch trials. Error: {e}\n")
            else:
                time.sleep(1)
