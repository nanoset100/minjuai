#!/usr/bin/env python3
"""정책개발팀 AI 에이전트 테스트"""

import json
from agents.policy_agent import PolicyAgent


def test_policy_agent():
    print("=== 정책개발팀 AI 테스트 ===\n")

    agent = PolicyAgent()

    # 1. 통계 확인
    stats = agent.get_proposal_stats()
    print(f"총 제안: {stats['total']}개")
    print(f"카테고리별: {json.dumps(stats['by_category'], ensure_ascii=False)}")

    # 2. 제안 목록
    proposals = agent.get_proposals()
    print(f"\n제안 목록:")
    for p in proposals:
        print(f"  - [{p['id']}] {p['title']} ({p['category']})")

    # 3. 새 제안 추가
    result = agent.submit_proposal(
        title="디지털 교육 강화",
        description="모든 학교에 AI 교육 도입",
        category="교육",
    )
    print(f"\n새 제안: {result['message']}")
    print(f"  ID: {result['proposal']['id']}")
    print(f"  제목: {result['proposal']['title']}")

    # 4. 잘못된 카테고리 테스트
    error_result = agent.submit_proposal(
        title="테스트",
        description="테스트",
        category="없는카테고리",
    )
    print(f"\n잘못된 카테고리: {error_result['error']}")

    # 5. 업데이트된 통계
    stats = agent.get_proposal_stats()
    print(f"\n업데이트된 통계: 총 {stats['total']}개")
    print(f"카테고리별: {json.dumps(stats['by_category'], ensure_ascii=False)}")

    print("\n=== 테스트 완료 ===")


if __name__ == "__main__":
    test_policy_agent()
