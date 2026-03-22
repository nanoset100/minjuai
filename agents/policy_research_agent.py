#!/usr/bin/env python3
"""
정책 연구 에이전트 (PolicyResearchAgent)
매주 1개 분야를 자동 연구하고 글로벌 비교 분석 후 정책안을 생성한다.
- GPT-4o mini 사용 (비용 최적화)

주간 사이클:
  월: 분야 선정 + 한국 현황 조사
  화~수: 글로벌 6개국 비교 연구
  목: AI 정책안 초안 생성
  금~토: 시민 토론 오픈
  일: 시민 의견 반영 → 최종 확정 → 온톨로지 저장
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(Path(__file__).parent.parent / "config" / ".env")


class PolicyResearchAgent:
    """주간 정책 자동 연구 에이전트"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    def _ai_call(self, system: str, prompt: str, max_tokens: int = 3000) -> str:
        """공통 AI 호출 함수"""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    # ─── 주간 사이클 ───

    def get_current_week_topic(self, db) -> Dict[str, Any]:
        """현재 주차의 정책 분야 반환"""
        now = datetime.now()
        week_number = now.isocalendar()[1]
        if week_number > 52:
            week_number = 52

        result = db.table("policy_topics").select("*").eq("week_number", week_number).execute()
        if result.data:
            return result.data[0]
        return {"week_number": week_number, "name": "미지정", "description": ""}

    def get_or_create_research(self, db, topic: Dict) -> Dict[str, Any]:
        """이번 주 연구 조회 또는 생성"""
        now = datetime.now()
        year = now.year
        week_number = topic["week_number"]

        result = db.table("weekly_research").select("*").eq("year", year).eq("week_number", week_number).execute()
        if result.data:
            return result.data[0]

        cycle = year - 2026 + 1
        result = db.table("weekly_research").insert({
            "topic_id": topic["id"],
            "year": year,
            "week_number": week_number,
            "cycle": cycle,
            "status": "researching",
            "phase": "mon_select",
        }).execute()
        return result.data[0]

    def research_korea_status(self, db, research_id: str, topic_name: str) -> Dict[str, Any]:
        """한국 현황 조사 (AI 분석)"""
        text = self._ai_call(
            system="""당신은 한국 정책 연구 전문가입니다.
주어진 분야에 대한 한국의 현재 상황을 객관적 데이터와 함께 분석하세요.

반드시 JSON 형식으로 응답하세요:
{
  "summary": "현황 요약 (3~5문장)",
  "key_stats": [
    {"label": "지표명", "value": "수치", "source": "출처"}
  ],
  "main_issues": [
    {"issue": "핵심 문제", "severity": "high/medium/low", "detail": "설명"}
  ],
  "current_policies": [
    {"name": "현행 정책명", "status": "시행중/폐지/논의중", "effectiveness": "효과 평가"}
  ],
  "public_opinion": "국민 여론 요약"
}""",
            prompt=f"분야: {topic_name}\n현재 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}\n\n한국의 현재 상황을 분석해주세요.",
        )

        # JSON 블록 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        try:
            korea_data = json.loads(text.strip())
        except json.JSONDecodeError:
            korea_data = {"summary": text, "key_stats": [], "main_issues": [], "current_policies": []}

        db.table("weekly_research").update({
            "korea_status": korea_data,
            "phase": "tue_wed_global",
        }).eq("id", research_id).execute()

        return korea_data

    def research_global_comparison(self, db, research_id: str, topic_name: str, korea_status: Dict) -> Dict[str, Any]:
        """글로벌 6개국 비교 연구"""
        korea_summary = korea_status.get("summary", "")

        text = self._ai_call(
            system="""당신은 글로벌 정책 비교 분석 전문가입니다.
주어진 분야에 대해 전세계 6개국 이상의 정책을 비교 분석하세요.
반드시 성공 사례와 실패 사례를 모두 포함하세요.

반드시 JSON 형식으로 응답하세요:
{
  "countries_analyzed": 6,
  "cases": [
    {
      "country": "국가명",
      "country_code": "ISO 코드 (예: KR, US, JP)",
      "flag": "국기 이모지",
      "policy_name": "정책명",
      "year_started": 2000,
      "description": "정책 설명",
      "outcome": "success/partial/failure",
      "key_metric": {"label": "핵심 지표", "value": "수치"},
      "lessons": "한국에 주는 교훈"
    }
  ],
  "best_practice": "한국에 가장 적합한 모델 추천",
  "recommended_combination": "최적 조합 (여러 국가 장점 결합)"
}""",
            prompt=f"""분야: {topic_name}

한국 현황 요약:
{korea_summary}

이 분야에서 전세계 6개국 이상의 정책 사례를 비교 분석해주세요.
성공 사례와 실패 사례를 모두 포함하고, 한국에 적용 가능한 최적 모델을 추천해주세요.""",
            max_tokens=4000,
        )

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        try:
            global_data = json.loads(text.strip())
        except json.JSONDecodeError:
            global_data = {"countries_analyzed": 0, "cases": [], "best_practice": text}

        db.table("weekly_research").update({
            "global_comparison": global_data,
            "phase": "thu_draft",
        }).eq("id", research_id).execute()

        # global_cases 테이블에도 저장
        for case in global_data.get("cases", []):
            try:
                db.table("global_cases").insert({
                    "country": case.get("country", ""),
                    "country_code": case.get("country_code", ""),
                    "policy_area": topic_name,
                    "policy_name": case.get("policy_name", ""),
                    "year_started": case.get("year_started"),
                    "description": case.get("description", ""),
                    "outcome": case.get("outcome", "partial"),
                    "outcome_detail": case.get("lessons", ""),
                    "key_metrics": case.get("key_metric", {}),
                    "lessons_learned": case.get("lessons", ""),
                    "applicability_to_korea": case.get("lessons", ""),
                }).execute()
            except Exception:
                pass

        return global_data

    def generate_policy_draft(self, db, research_id: str, topic_name: str,
                              korea_status: Dict, global_comparison: Dict) -> Dict[str, Any]:
        """정책안 초안 AI 자동 생성"""
        text = self._ai_call(
            system="""당신은 AI 정당의 수석 정책 연구원입니다.
한국 현황과 글로벌 비교 분석을 바탕으로 구체적이고 실현 가능한 정책안을 작성하세요.

반드시 JSON 형식으로 응답하세요:
{
  "title": "정책안 제목",
  "subtitle": "부제",
  "summary": "정책 요약 (3문장)",
  "background": "배경 및 필요성",
  "global_reference": "참고한 해외 사례와 적용 방법",
  "key_proposals": [
    {
      "proposal": "세부 제안",
      "timeline": "단기/중기/장기",
      "budget": "예산 추정",
      "expected_effect": "예상 효과"
    }
  ],
  "total_budget": "총 예산 추정",
  "feasibility_score": 75,
  "risks": ["리스크 1", "리스크 2"],
  "implementation_steps": [
    {"step": 1, "action": "행동", "timeline": "기간"}
  ]
}""",
            prompt=f"""분야: {topic_name}

한국 현황:
{korea_status.get('summary', '')}

주요 문제:
{', '.join([i.get('issue', '') for i in korea_status.get('main_issues', [])])}

글로벌 최적 모델:
{global_comparison.get('recommended_combination', '')}

해외 성공 사례:
{', '.join([f"{c.get('country', '')}: {c.get('policy_name', '')}" for c in global_comparison.get('cases', []) if c.get('outcome') == 'success'])}

위 분석을 바탕으로 한국에 맞는 구체적 정책안을 작성해주세요.""",
            max_tokens=4000,
        )

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        try:
            draft = json.loads(text.strip())
        except json.JSONDecodeError:
            draft = {"title": topic_name + " 정책안", "summary": text, "feasibility_score": 50}

        # 정책안 텍스트 생성
        draft_text = f"""# {draft.get('title', '')}
{draft.get('subtitle', '')}

## 요약
{draft.get('summary', '')}

## 배경
{draft.get('background', '')}

## 해외 사례 참고
{draft.get('global_reference', '')}

## 세부 제안
"""
        for p in draft.get("key_proposals", []):
            draft_text += f"\n### {p.get('proposal', '')}\n"
            draft_text += f"- 시기: {p.get('timeline', '')}\n"
            draft_text += f"- 예산: {p.get('budget', '')}\n"
            draft_text += f"- 효과: {p.get('expected_effect', '')}\n"

        draft_text += f"\n## 총 예산: {draft.get('total_budget', '미정')}\n"
        draft_text += f"## 실현가능성: {draft.get('feasibility_score', 50)}%\n"

        db.table("weekly_research").update({
            "policy_draft": draft_text,
            "feasibility_score": draft.get("feasibility_score", 50),
            "budget_estimate": draft.get("total_budget", ""),
            "expected_effect": draft.get("summary", ""),
            "status": "draft",
            "phase": "fri_sat_review",
        }).eq("id", research_id).execute()

        return draft

    def run_full_cycle(self, db) -> Dict[str, Any]:
        """전체 주간 연구 사이클 실행"""
        topic = self.get_current_week_topic(db)
        topic_name = topic["name"]

        research = self.get_or_create_research(db, topic)
        research_id = research["id"]

        korea = self.research_korea_status(db, research_id, topic_name)
        global_comp = self.research_global_comparison(db, research_id, topic_name, korea)
        draft = self.generate_policy_draft(db, research_id, topic_name, korea, global_comp)

        self._create_ontology_nodes(db, research_id, topic_name, korea, global_comp, draft)

        db.table("agent_activities").insert({
            "agent_id": "policy_research",
            "action": f"주간 정책 연구: {topic_name}",
            "detail": f"한국 현황 조사 + {global_comp.get('countries_analyzed', 0)}개국 비교 + 정책안 생성 완료",
            "status": "success",
            "result_summary": draft.get("title", ""),
            "metadata": {"topic": topic_name, "week": topic["week_number"], "feasibility": draft.get("feasibility_score", 0)},
        }).execute()

        return {
            "topic": topic_name,
            "week": topic["week_number"],
            "research_id": research_id,
            "korea_status": korea,
            "global_comparison": global_comp,
            "policy_draft": draft,
            "status": "draft",
        }

    def _create_ontology_nodes(self, db, research_id, topic_name, korea, global_comp, draft):
        """연구 결과를 온톨로지 노드/엣지로 변환"""
        for issue in korea.get("main_issues", []):
            try:
                db.table("ontology_nodes").insert({
                    "type": "issue",
                    "name": issue.get("issue", ""),
                    "description": issue.get("detail", ""),
                    "data": {"severity": issue.get("severity", "medium")},
                    "research_id": research_id,
                    "country": "KR",
                }).execute()
            except Exception:
                pass

        try:
            db.table("ontology_nodes").insert({
                "type": "policy",
                "name": draft.get("title", topic_name),
                "description": draft.get("summary", ""),
                "data": {
                    "feasibility_score": draft.get("feasibility_score", 0),
                    "budget": draft.get("total_budget", ""),
                },
                "research_id": research_id,
                "country": "KR",
            }).execute()
        except Exception:
            pass

        for case in global_comp.get("cases", []):
            try:
                db.table("ontology_nodes").insert({
                    "type": "global_case",
                    "name": f"{case.get('country', '')} - {case.get('policy_name', '')}",
                    "description": case.get("description", ""),
                    "data": {"outcome": case.get("outcome", ""), "key_metric": case.get("key_metric", {})},
                    "research_id": research_id,
                    "country": case.get("country_code", ""),
                }).execute()
            except Exception:
                pass

    # ─── 솔루션 엔진 ───

    def solve_policy_question(self, db, question: str) -> Dict[str, Any]:
        """시민 질문에 대해 온톨로지 기반 솔루션 도출"""
        all_research = db.table("weekly_research").select(
            "*, policy_topics(name, category_group)"
        ).eq("status", "draft").execute()

        existing_policies = []
        for r in (all_research.data or []):
            topic = r.get("policy_topics", {})
            if topic:
                existing_policies.append(f"- {topic.get('name', '')}: {r.get('expected_effect', '')[:100]}")

        global_result = db.table("global_cases").select("country, policy_name, policy_area, outcome, lessons_learned").limit(20).execute()
        global_context = "\n".join([
            f"- {g['country']} '{g['policy_name']}' ({g['policy_area']}): {g.get('outcome', '')} - {(g.get('lessons_learned') or '')[:80]}"
            for g in (global_result.data or [])
        ])

        solution_text = self._ai_call(
            system="""당신은 AI 정당의 정책 솔루션 엔진입니다.
시민의 질문에 대해 근거 기반 해법을 제시하세요.

응답 형식:
1. 문제 정의 (데이터 기반, 2~3문장)
2. 글로벌 사례 (최소 3개국, 각 1~2문장)
3. AI 솔루션 (단기/중기/장기 구분)
4. 실현가능성 점수 (0~100)
5. 예산 추정

관련 기존 정책이 있으면 연결해서 시너지를 설명하세요.""",
            prompt=f"""시민 질문: {question}

기존 연구된 정책:
{chr(10).join(existing_policies[:10]) if existing_policies else '아직 없음'}

글로벌 사례 DB:
{global_context if global_context else '아직 없음'}

이 질문에 대한 근거 기반 솔루션을 제시해주세요.""",
        )

        try:
            db.table("agent_activities").insert({
                "agent_id": "solution_engine",
                "action": "정책 솔루션 도출",
                "detail": question[:200],
                "status": "success",
                "result_summary": solution_text[:200],
            }).execute()
        except Exception:
            pass

        return {
            "question": question,
            "solution": solution_text,
            "related_research_count": len(all_research.data or []),
            "global_cases_referenced": len(global_result.data or []),
        }
