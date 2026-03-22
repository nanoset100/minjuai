#!/usr/bin/env python3
"""
AI 정당 정책개발팀 에이전트
정책 제안 접수 및 관리 시스템 (간단 버전)
"""

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "config" / ".env")


class PolicyAgent:
    """
    정책개발팀 AI 에이전트

    기능:
    - 정책 제안 접수
    - 제안 목록 조회
    - 카테고리별 통계
    """

    CATEGORIES = ["경제", "복지", "교육", "환경", "교통"]

    SEED_DATA = [
        {
            "title": "AI 기본소득 정책",
            "description": "AI 자동화로 인한 실업 대비, 모든 시민에게 월 50만원 AI 기본소득 지급. AI 기업 수익의 10%를 재원으로 활용.",
            "category": "경제",
        },
        {
            "title": "청년 주거 지원",
            "description": "만 19~34세 청년 대상 공공임대주택 5만호 공급 및 월세 보조금 30만원 지원.",
            "category": "복지",
        },
        {
            "title": "탄소중립 2030",
            "description": "2030년까지 탄소 배출 50% 감축. 전기차 보조금 확대, 신재생에너지 비중 40% 달성 목표.",
            "category": "환경",
        },
    ]

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data" / "policies"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.proposals_file = self.data_dir / "proposals.json"

        if not self.proposals_file.exists():
            self._init_seed_data()

    def _init_seed_data(self):
        proposals = []
        for seed in self.SEED_DATA:
            proposal = {
                "id": str(uuid.uuid4())[:8],
                "title": seed["title"],
                "description": seed["description"],
                "category": seed["category"],
                "created_at": datetime.now().isoformat(),
                "status": "접수",
            }
            proposals.append(proposal)
        self._save(proposals)

    def _load(self) -> List[Dict[str, Any]]:
        if not self.proposals_file.exists():
            return []
        with open(self.proposals_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, proposals: List[Dict[str, Any]]):
        with open(self.proposals_file, "w", encoding="utf-8") as f:
            json.dump(proposals, f, ensure_ascii=False, indent=2)

    def submit_proposal(self, title: str, description: str, category: str) -> Dict[str, Any]:
        if category not in self.CATEGORIES:
            return {"error": f"유효하지 않은 카테고리입니다. 가능한 카테고리: {self.CATEGORIES}"}

        proposal = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "description": description,
            "category": category,
            "created_at": datetime.now().isoformat(),
            "status": "접수",
        }

        proposals = self._load()
        proposals.append(proposal)
        self._save(proposals)

        return {"message": "제안이 접수되었습니다.", "proposal": proposal}

    def get_proposals(self) -> List[Dict[str, Any]]:
        return self._load()

    def analyze_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Claude AI로 정책 제안 실현가능성 분석"""
        proposals = self._load()
        proposal = next((p for p in proposals if p["id"] == proposal_id), None)
        if not proposal:
            return {"error": "제안을 찾을 수 없습니다."}

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OPENAI_API_KEY가 설정되지 않았습니다."}

        client = OpenAI(api_key=api_key)

        prompt = f"""다음 정책 제안을 분석해주세요:

제목: {proposal['title']}
내용: {proposal['description']}
카테고리: {proposal['category']}

다음 항목을 JSON 형식으로만 답변해주세요 (설명 없이 JSON만):
{{
    "feasibility_score": 0부터 100 사이의 점수,
    "summary": "한줄 요약",
    "budget_estimate": "예상 예산",
    "expected_beneficiaries": "예상 수혜자",
    "pros": ["장점1", "장점2"],
    "cons": ["단점1", "단점2"],
    "recommendations": ["개선 제안1", "개선 제안2"]
}}"""

        try:
            message = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            raw_text = message.choices[0].message.content
            # ```json ... ``` 코드블록 제거
            cleaned = re.sub(r"```(?:json)?\s*", "", raw_text).strip()
            cleaned = cleaned.rstrip("`").strip()
            analysis = json.loads(cleaned)

        except json.JSONDecodeError:
            analysis = {"raw_response": raw_text, "parse_error": True}
        except Exception as e:
            return {"error": f"AI 분석 실패: {str(e)}"}

        # proposals.json에 분석 결과 저장
        for p in proposals:
            if p["id"] == proposal_id:
                p["analysis"] = analysis
                p["status"] = "분석완료"
                p["analyzed_at"] = datetime.now().isoformat()
        self._save(proposals)

        return {"proposal_id": proposal_id, "analysis": analysis}

    def analyze_proposal_data(self, title: str, description: str, category: str) -> Dict[str, Any]:
        """Supabase에서 호출용 — 제목/내용/카테고리로 직접 AI 분석"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OPENAI_API_KEY가 설정되지 않았습니다."}

        client = OpenAI(api_key=api_key)

        prompt = f"""다음 정책 제안을 분석해주세요:

제목: {title}
내용: {description}
카테고리: {category}

다음 항목을 JSON 형식으로만 답변해주세요 (설명 없이 JSON만):
{{
    "feasibility_score": 0부터 100 사이의 점수,
    "summary": "한줄 요약",
    "budget_estimate": "예상 예산",
    "expected_beneficiaries": "예상 수혜자",
    "pros": ["장점1", "장점2"],
    "cons": ["단점1", "단점2"],
    "recommendations": ["개선 제안1", "개선 제안2"]
}}"""

        try:
            message = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            raw_text = message.choices[0].message.content
            cleaned = re.sub(r"```(?:json)?\s*", "", raw_text).strip()
            cleaned = cleaned.rstrip("`").strip()
            analysis = json.loads(cleaned)
            return analysis

        except json.JSONDecodeError:
            return {"raw_response": raw_text, "parse_error": True, "feasibility_score": 0}
        except Exception as e:
            return {"error": f"AI 분석 실패: {str(e)}", "feasibility_score": 0}

    def get_proposal_stats(self) -> Dict[str, Any]:
        proposals = self._load()
        total = len(proposals)

        category_counts = {}
        for cat in self.CATEGORIES:
            category_counts[cat] = 0
        for p in proposals:
            cat = p.get("category", "기타")
            if cat in category_counts:
                category_counts[cat] += 1

        return {
            "total": total,
            "by_category": category_counts,
        }


if __name__ == "__main__":
    agent = PolicyAgent()

    print("=== 정책개발팀 AI 에이전트 ===\n")

    stats = agent.get_proposal_stats()
    print(f"총 제안 수: {stats['total']}")
    print(f"카테고리별: {json.dumps(stats['by_category'], ensure_ascii=False)}\n")

    print("--- 기존 제안 목록 ---")
    for p in agent.get_proposals():
        print(f"  [{p['id']}] {p['title']} ({p['category']})")

    print("\n--- 새 제안 접수 ---")
    result = agent.submit_proposal(
        title="AI 교육 혁신",
        description="초중고 AI 리터러시 교육 의무화 및 AI 튜터 시스템 도입",
        category="교육",
    )
    print(f"  결과: {result['message']}")
    print(f"  ID: {result['proposal']['id']}")

    print("\n--- 업데이트된 통계 ---")
    stats = agent.get_proposal_stats()
    print(f"총 제안 수: {stats['total']}")
    print(f"카테고리별: {json.dumps(stats['by_category'], ensure_ascii=False)}")
