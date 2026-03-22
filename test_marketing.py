#!/usr/bin/env python3
"""
MarketingAgent 테스트 코드
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from agents.marketing_agent import MarketingAgent
from loguru import logger


async def test_create_post():
    """단일 포스트 생성 테스트"""
    logger.info("=" * 50)
    logger.info("테스트 1: 단일 포스트 생성")
    logger.info("=" * 50)

    agent = MarketingAgent()

    # 트위터 포스트
    twitter_post = await agent.create_post("AI 투명성과 정치 혁신", "twitter")
    if twitter_post:
        logger.info(f"✅ 트위터 포스트 생성 성공")
        logger.info(f"  내용: {twitter_post['content']}")
        logger.info(f"  글자수: {len(twitter_post['content'])}/280")
        logger.info(f"  해시태그: {' '.join(twitter_post['hashtags'])}")
        logger.info(f"  톤: {twitter_post['tone']}")
        assert len(twitter_post['content']) <= 280, "트위터 글자수 초과!"
    else:
        logger.error("❌ 트위터 포스트 생성 실패")

    # 인스타그램 포스트
    insta_post = await agent.create_post("청년 정치 참여", "instagram")
    if insta_post:
        logger.info(f"\n✅ 인스타그램 포스트 생성 성공")
        logger.info(f"  내용: {insta_post['content'][:100]}...")
        logger.info(f"  글자수: {len(insta_post['content'])}/2200")
        logger.info(f"  해시태그: {' '.join(insta_post['hashtags'])}")
        logger.info(f"  이미지 제안: {insta_post.get('image_suggestion', 'N/A')}")
        assert len(insta_post['content']) <= 2200, "인스타그램 글자수 초과!"
    else:
        logger.error("❌ 인스타그램 포스트 생성 실패")

    return twitter_post, insta_post


async def test_hashtag_optimization():
    """해시태그 최적화 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 2: 해시태그 최적화")
    logger.info("=" * 50)

    agent = MarketingAgent()

    test_content = "AI 기술로 더 투명한 정치를 만들어갑니다. 시민 여러분의 참여가 민주주의를 완성합니다."

    # 트위터 해시태그 (최대 5개)
    twitter_tags = await agent.optimize_hashtags(test_content, "twitter")
    logger.info(f"트위터 해시태그 ({len(twitter_tags)}개): {' '.join(twitter_tags)}")
    assert len(twitter_tags) <= 5, f"트위터 해시태그 초과: {len(twitter_tags)}개"

    # 인스타그램 해시태그 (최대 30개)
    insta_tags = await agent.optimize_hashtags(test_content, "instagram")
    logger.info(f"인스타그램 해시태그 ({len(insta_tags)}개): {' '.join(insta_tags)}")
    assert len(insta_tags) <= 30, f"인스타그램 해시태그 초과: {len(insta_tags)}개"

    # 모든 태그가 # 으로 시작하는지 확인
    all_tags = twitter_tags + insta_tags
    for tag in all_tags:
        assert tag.startswith("#"), f"해시태그 형식 오류: {tag}"

    logger.info("✅ 해시태그 최적화 테스트 통과")
    return twitter_tags, insta_tags


async def test_daily_content():
    """일일 콘텐츠 생성 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 3: 일일 콘텐츠 자동 생성")
    logger.info("=" * 50)

    agent = MarketingAgent()
    posts = await agent.generate_daily_content()

    logger.info(f"생성된 포스트 수: {len(posts)}")
    assert 3 <= len(posts) <= 5, f"포스트 수 범위 초과: {len(posts)}"

    for i, post in enumerate(posts):
        logger.info(f"\n--- 포스트 {i+1} ---")
        logger.info(f"  플랫폼: {post['platform']}")
        logger.info(f"  주제: {post['topic']}")
        logger.info(f"  내용: {post['content'][:80]}...")
        logger.info(f"  해시태그: {len(post['hashtags'])}개")
        logger.info(f"  상태: {post['status']}")
        logger.info(f"  예약시간: {post.get('scheduled_at', 'N/A')}")

    logger.info(f"\n✅ 일일 콘텐츠 테스트 통과 ({len(posts)}개 생성)")
    return posts


async def test_schedule():
    """스케줄링 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 4: 포스트 스케줄링")
    logger.info("=" * 50)

    agent = MarketingAgent()

    # 포스트 2개 생성
    await agent.create_post("디지털 민주주의", "twitter")
    await agent.create_post("시민 참여형 정책", "instagram")

    # 스케줄링
    scheduled = await agent.schedule_posts()
    logger.info(f"스케줄된 포스트: {len(scheduled)}개")

    for post in scheduled:
        assert post['status'] == 'scheduled', f"상태 오류: {post['status']}"
        assert 'scheduled_at' in post, "예약 시간 누락"
        logger.info(f"  [{post['platform']}] {post['scheduled_at']}")

    logger.info("✅ 스케줄링 테스트 통과")
    return scheduled


async def test_performance_stats():
    """성과 통계 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 5: 성과 통계")
    logger.info("=" * 50)

    agent = MarketingAgent()

    # 포스트 생성 후 통계 확인
    await agent.create_post("AI 정치 혁신", "twitter")
    await agent.create_post("교육 혁신", "instagram")

    stats = agent.get_performance_stats()
    logger.info(f"통계:\n{json.dumps(stats, indent=2, ensure_ascii=False)}")

    assert 'summary' in stats, "summary 키 누락"
    assert 'platforms' in stats, "platforms 키 누락"
    assert stats['summary']['total_posts'] == 2, f"포스트 수 불일치: {stats['summary']['total_posts']}"

    logger.info("✅ 성과 통계 테스트 통과")
    return stats


async def test_marketing_report():
    """마케팅 리포트 생성 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 6: 마케팅 리포트 생성")
    logger.info("=" * 50)

    agent = MarketingAgent()

    # 포스트 생성
    await agent.create_post("공정한 경제 정책", "twitter")
    await agent.create_post("주거 안정 정책", "instagram")

    report = agent.get_marketing_report()
    logger.info(f"리포트 미리보기:\n{report[:500]}...")

    assert "마케팅 에이전트 일일 리포트" in report, "리포트 제목 누락"
    assert "TWITTER" in report, "트위터 섹션 누락"
    assert "INSTAGRAM" in report, "인스타그램 섹션 누락"

    logger.info("✅ 마케팅 리포트 테스트 통과")
    return report


async def test_invalid_platform():
    """잘못된 플랫폼 처리 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("테스트 7: 잘못된 플랫폼 처리")
    logger.info("=" * 50)

    agent = MarketingAgent()
    result = await agent.create_post("테스트", "tiktok")
    assert result is None, "잘못된 플랫폼에서 None 반환되어야 함"

    logger.info("✅ 잘못된 플랫폼 처리 테스트 통과")


async def run_all_tests():
    """전체 테스트 실행"""
    logger.info("🧪 MarketingAgent 전체 테스트 시작")
    logger.info(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'errors': [],
    }

    tests = [
        ("단일 포스트 생성", test_create_post),
        ("해시태그 최적화", test_hashtag_optimization),
        ("일일 콘텐츠 생성", test_daily_content),
        ("포스트 스케줄링", test_schedule),
        ("성과 통계", test_performance_stats),
        ("마케팅 리포트", test_marketing_report),
        ("잘못된 플랫폼 처리", test_invalid_platform),
    ]

    for name, test_func in tests:
        results['total'] += 1
        try:
            await test_func()
            results['passed'] += 1
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({'test': name, 'error': str(e)})
            logger.error(f"❌ 테스트 실패 [{name}]: {e}")

    # 결과 요약
    logger.info("\n" + "=" * 60)
    logger.info("🧪 테스트 결과 요약")
    logger.info("=" * 60)
    logger.info(f"  총 테스트: {results['total']}")
    logger.info(f"  ✅ 성공: {results['passed']}")
    logger.info(f"  ❌ 실패: {results['failed']}")

    if results['errors']:
        logger.info("\n실패한 테스트:")
        for err in results['errors']:
            logger.info(f"  - {err['test']}: {err['error']}")

    if results['failed'] == 0:
        logger.info("\n🎉 모든 테스트 통과!")
    else:
        logger.warning(f"\n⚠️ {results['failed']}개 테스트 실패")

    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
