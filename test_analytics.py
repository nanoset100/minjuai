#!/usr/bin/env python3
"""
AnalyticsAgent 테스트 코드
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from agents.analytics_agent import AnalyticsAgent
from loguru import logger


async def test_stats_update():
    """통계 업데이트 테스트: 숫자가 증가하는지 검증"""
    logger.info("=" * 50)
    logger.info("테스트 1: 실시간 통계 업데이트")
    logger.info("=" * 50)

    agent = AnalyticsAgent()

    # 첫 번째 업데이트
    stats1 = await agent.update_real_time_stats()
    members1 = stats1["members"]["total"]

    # 두 번째 업데이트
    stats2 = await agent.update_real_time_stats()
    members2 = stats2["members"]["total"]

    logger.info(f"  첫 번째: {members1:,}명")
    logger.info(f"  두 번째: {members2:,}명")
    assert members2 >= members1, f"당원 수가 감소함: {members1} -> {members2}"

    # 필수 키 검증
    assert "members" in stats2
    assert "social" in stats2
    assert "policies" in stats2
    assert "support" in stats2
    assert "twitter_followers" in stats2["social"]
    assert "instagram_followers" in stats2["social"]
    assert "youtube_subscribers" in stats2["social"]

    logger.info("✅ 통계 업데이트 테스트 통과")
    return stats2


async def test_trend_analysis():
    """트렌드 분석 테스트: 성장률 계산 검증"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 2: 트렌드 분석")
    logger.info("=" * 50)

    agent = AnalyticsAgent()
    trends = await agent.analyze_trends()

    logger.info(f"  주간 성장률: {trends['weekly_growth_rate']}%")
    logger.info(f"  월간 성장률: {trends['monthly_growth_rate']}%")
    logger.info(f"  피크 시간: {trends['peak_hours']}")
    logger.info(f"  인기 카테고리: {[c['category'] for c in trends['popular_categories'][:3]]}")

    # 구조 검증
    assert "weekly_growth_rate" in trends
    assert "monthly_growth_rate" in trends
    assert "popular_categories" in trends
    assert "peak_hours" in trends
    assert "region_interest" in trends

    # 타입 검증
    assert isinstance(trends["weekly_growth_rate"], (int, float))
    assert isinstance(trends["monthly_growth_rate"], (int, float))
    assert isinstance(trends["popular_categories"], list)
    assert len(trends["popular_categories"]) > 0

    # 지역 데이터 검증
    assert len(trends["region_interest"]) > 0
    for region, info in trends["region_interest"].items():
        assert "members" in info
        assert "share" in info

    logger.info("✅ 트렌드 분석 테스트 통과")
    return trends


async def test_election_prediction():
    """선거 예측 테스트: 시나리오별 검증"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 3: 선거 예측")
    logger.info("=" * 50)

    agent = AnalyticsAgent()
    predictions = await agent.predict_election_outcome()

    logger.info(f"  현재 지지율: {predictions['current_support_rate']}%")
    logger.info(f"  목표 달성률: {predictions['progress_percent']}%")
    logger.info(f"  선거까지: D-{predictions['days_until_election']}")
    logger.info(f"  필요 월간 성장률: {predictions['required_monthly_growth']}%")

    # 구조 검증
    assert "current_support_rate" in predictions
    assert "target_seats" in predictions
    assert "progress_percent" in predictions
    assert "days_until_election" in predictions
    assert "scenarios" in predictions

    # 시나리오 검증
    scenarios = predictions["scenarios"]
    assert "optimistic" in scenarios
    assert "neutral" in scenarios
    assert "pessimistic" in scenarios

    for name, scenario in scenarios.items():
        assert "support_rate" in scenario, f"{name}: support_rate 누락"
        assert "seats" in scenario, f"{name}: seats 누락"
        assert "probability" in scenario, f"{name}: probability 누락"
        logger.info(f"  [{name}] 지지율={scenario['support_rate']}%, 의석={scenario['seats']}, 확률={scenario['probability']}")

    # 확률 합 검증 (대략 1.0)
    total_prob = sum(s["probability"] for s in scenarios.values())
    assert 0.9 <= total_prob <= 1.1, f"확률 합 오류: {total_prob}"

    # 지지율 범위 검증
    assert 0 <= predictions["current_support_rate"] <= 100
    assert predictions["days_until_election"] > 0

    logger.info("✅ 선거 예측 테스트 통과")
    return predictions


async def test_analytics_report():
    """분석 리포트 생성 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 4: 분석 리포트 생성")
    logger.info("=" * 50)

    agent = AnalyticsAgent()
    report = await agent.generate_analytics_report()

    logger.info(f"  리포트 길이: {len(report)}자")
    logger.info(f"  미리보기:\n{report[:300]}...")

    # 마크다운 구조 검증
    assert "# 📊 데이터분석 주간 리포트" in report
    assert "핵심 지표" in report
    assert "성장 트렌드" in report
    assert "선거 예측" in report
    assert "권장 사항" in report

    # 파일 저장 검증
    output_dir = Path(__file__).parent / "data" / "outputs"
    today = datetime.now().strftime("%Y%m%d")
    report_file = output_dir / f"analytics_report_{today}.md"
    assert report_file.exists(), f"리포트 파일이 없음: {report_file}"

    logger.info("✅ 분석 리포트 테스트 통과")
    return report


async def test_constituency_analysis():
    """선거구 분석 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 5: 선거구 분석")
    logger.info("=" * 50)

    agent = AnalyticsAgent()
    result = await agent.get_constituency_analysis()

    logger.info(f"  분석 선거구 수: {result['analyzed']}")
    logger.info(f"  상위 타겟 수: {len(result['top_targets'])}")

    assert result["total_constituencies"] == 300
    assert result["analyzed"] > 0
    assert len(result["top_targets"]) <= 10

    for target in result["top_targets"][:3]:
        assert "constituency" in target
        assert "priority_score" in target
        assert "strategy" in target
        logger.info(f"  {target['constituency']}: 점수={target['priority_score']}, 전략={target['strategy'][:20]}...")

    # 정렬 검증 (점수 내림차순)
    scores = [t["priority_score"] for t in result["top_targets"]]
    assert scores == sorted(scores, reverse=True), "우선순위 정렬 오류"

    logger.info("✅ 선거구 분석 테스트 통과")
    return result


async def test_cache():
    """캐시 동작 검증"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 6: 캐시 동작")
    logger.info("=" * 50)

    agent = AnalyticsAgent()

    # 캐시 비어있어야 함
    cached = agent.get_cached_stats()
    assert cached is None, "초기 캐시가 비어있지 않음"

    # 업데이트 후 캐시 존재
    await agent.update_real_time_stats()
    cached = agent.get_cached_stats()
    assert cached is not None, "업데이트 후 캐시가 없음"
    assert "members" in cached

    logger.info("✅ 캐시 테스트 통과")


async def test_data_persistence():
    """데이터 영속성 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 7: 데이터 영속성")
    logger.info("=" * 50)

    agent1 = AnalyticsAgent()
    await agent1.update_real_time_stats()
    total1 = agent1.members["total"]

    # 새 인스턴스로 로드
    agent2 = AnalyticsAgent()
    total2 = agent2.members["total"]

    logger.info(f"  agent1 당원: {total1:,}")
    logger.info(f"  agent2 당원: {total2:,}")
    assert total2 == total1, f"데이터 불일치: {total1} vs {total2}"

    logger.info("✅ 데이터 영속성 테스트 통과")


async def run_all_tests():
    """전체 테스트 실행"""
    logger.info("🧪 AnalyticsAgent 전체 테스트 시작")
    logger.info(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    results = {"total": 0, "passed": 0, "failed": 0, "errors": []}

    tests = [
        ("실시간 통계 업데이트", test_stats_update),
        ("트렌드 분석", test_trend_analysis),
        ("선거 예측", test_election_prediction),
        ("분석 리포트 생성", test_analytics_report),
        ("선거구 분석", test_constituency_analysis),
        ("캐시 동작", test_cache),
        ("데이터 영속성", test_data_persistence),
    ]

    for name, test_func in tests:
        results["total"] += 1
        try:
            await test_func()
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"test": name, "error": str(e)})
            logger.error(f"❌ 테스트 실패 [{name}]: {e}")

    # 결과 요약
    logger.info("\n" + "=" * 60)
    logger.info("🧪 테스트 결과 요약")
    logger.info("=" * 60)
    logger.info(f"  총 테스트: {results['total']}")
    logger.info(f"  ✅ 성공: {results['passed']}")
    logger.info(f"  ❌ 실패: {results['failed']}")

    if results["errors"]:
        logger.info("\n실패한 테스트:")
        for err in results["errors"]:
            logger.info(f"  - {err['test']}: {err['error']}")

    if results["failed"] == 0:
        logger.info("\n🎉 모든 테스트 통과!")
    else:
        logger.warning(f"\n⚠️ {results['failed']}개 테스트 실패")

    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
