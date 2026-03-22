"""
Batch API 헬퍼
Anthropic Message Batches API를 활용한 비동기 배치 처리

비용 절감: 동일 모델 대비 50% 할인
처리 시간: 최대 24시간 (비실시간 작업에 적합)
적용 대상: weekly_strategy (주 1회, 비실시간)

API: client.messages.batches.create() / .retrieve() / .results()
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from loguru import logger

load_dotenv(Path(__file__).parent.parent / "config" / ".env")


class BatchHelper:
    """
    Anthropic Batch API 래퍼

    사용 흐름:
        1. submit_weekly_strategy() → batch_id 반환
        2. (최대 24시간 대기)
        3. get_result(batch_id) → 결과 반환 or None(미완료)
    """

    # 모델별 비용 (per 1M tokens, Batch 50% 할인 적용 후)
    # Haiku:  입력 $0.40, 출력 $2.00
    # Sonnet: 입력 $1.50, 출력 $7.50
    # Opus:   입력 $7.50, 출력 $37.50

    STRATEGY_MODEL = "claude-haiku-4-5-20251001"  # 비용 절감 위해 Haiku 통일
    BATCH_STATE_FILE = "batch_state.json"

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.state_dir = Path(__file__).parent.parent / "data" / "monitoring"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / self.BATCH_STATE_FILE

    def _load_state(self) -> dict:
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_state(self, state: dict):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def submit_weekly_strategy(self) -> str:
        """
        주간 전략 보고서를 Batch API로 제출

        Returns:
            batch_id: 배치 작업 ID (결과 조회에 사용)
        """
        now = datetime.now()
        custom_id = f"weekly-strategy-{now.strftime('%Y%m%d')}"

        batch = self.client.messages.batches.create(
            requests=[
                {
                    "custom_id": custom_id,
                    "params": {
                        "model": self.STRATEGY_MODEL,
                        "max_tokens": 3000,
                        "system": (
                            "당신은 AI 정당의 전략기획실장입니다.\n"
                            "2028년 4월 선거에서 10석을 목표로 합니다.\n\n"
                            "주간 전략 회의 보고서를 작성하세요:\n"
                            "1. 이번 주 진행 상황\n"
                            "2. 다음 주 주요 전략\n"
                            "3. 리스크 요인\n"
                            "4. 기회 요인\n"
                            "5. 대표의 결정이 필요한 사항"
                        ),
                        "messages": [
                            {
                                "role": "user",
                                "content": (
                                    f"현재: {now.strftime('%Y년 %m월 %d일')}\n"
                                    f"선거일까지: {(datetime(2028, 4, 10) - now).days}일\n\n"
                                    "주간 전략 보고서를 작성해주세요."
                                ),
                            }
                        ],
                    },
                }
            ]
        )

        # 배치 상태 저장
        state = self._load_state()
        state["weekly_strategy"] = {
            "batch_id": batch.id,
            "custom_id": custom_id,
            "submitted_at": now.isoformat(),
            "status": "submitted",
        }
        self._save_state(state)

        logger.info(f"Batch 제출 완료: {batch.id} (weekly_strategy)")
        return batch.id

    def get_result(self, batch_id: str) -> Optional[str]:
        """
        Batch 결과 조회

        Args:
            batch_id: 배치 작업 ID

        Returns:
            결과 텍스트 (완료 시) / None (미완료 또는 실패)
        """
        batch = self.client.messages.batches.retrieve(batch_id)

        if batch.processing_status != "ended":
            logger.info(f"Batch {batch_id}: 처리 중 ({batch.processing_status})")
            return None

        # 결과 확인
        if batch.request_counts.succeeded == 0:
            logger.warning(f"Batch {batch_id}: 성공한 요청 없음 (실패: {batch.request_counts.errored})")
            return None

        # 결과 스트림에서 텍스트 추출
        results = self.client.messages.batches.results(batch_id)
        for entry in results:
            if entry.result.type == "succeeded":
                text = entry.result.message.content[0].text
                logger.info(f"Batch {batch_id}: 결과 수신 완료")

                # 상태 업데이트
                state = self._load_state()
                if "weekly_strategy" in state and state["weekly_strategy"]["batch_id"] == batch_id:
                    state["weekly_strategy"]["status"] = "completed"
                    state["weekly_strategy"]["completed_at"] = datetime.now().isoformat()
                    self._save_state(state)

                return text

        return None

    def get_weekly_strategy_result(self) -> Optional[str]:
        """
        가장 최근 weekly_strategy 배치 결과 조회 (편의 메서드)

        Returns:
            결과 텍스트 / None
        """
        state = self._load_state()
        ws = state.get("weekly_strategy")

        if not ws or ws.get("status") == "completed":
            return None

        return self.get_result(ws["batch_id"])

    def get_batch_status(self) -> dict:
        """현재 배치 상태 조회"""
        state = self._load_state()
        result = {}

        for task_name, info in state.items():
            batch_id = info.get("batch_id")
            if not batch_id:
                continue

            try:
                batch = self.client.messages.batches.retrieve(batch_id)
                result[task_name] = {
                    "batch_id": batch_id,
                    "processing_status": batch.processing_status,
                    "succeeded": batch.request_counts.succeeded,
                    "errored": batch.request_counts.errored,
                    "submitted_at": info.get("submitted_at"),
                }
            except Exception as e:
                result[task_name] = {
                    "batch_id": batch_id,
                    "error": str(e),
                }

        return result
