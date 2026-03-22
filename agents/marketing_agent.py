#!/usr/bin/env python3
"""
AI 정당 마케팅 에이전트
SNS 콘텐츠 자동 생성 및 관리 시스템
"""

import asyncio
import hashlib
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import os

from openai import OpenAI
from dotenv import load_dotenv
from loguru import logger

# 환경 변수 로드
load_dotenv(Path(__file__).parent.parent / "config" / ".env")


class MarketingAgent:
    """
    SNS 마케팅 자동화 에이전트

    기능:
    - SNS 콘텐츠 자동 생성 (트위터, 인스타그램)
    - Claude API로 정치 관련 포스트 작성
    - 매일 3-5개 포스트 자동 생성
    - 해시태그 자동 최적화
    - 포스팅 스케줄 관리
    - 성과 추적 (좋아요, 공유)
    """

    # 플랫폼별 제약 조건
    PLATFORM_LIMITS = {
        "twitter": {
            "max_length": 280,
            "max_hashtags": 5,
            "image_ratio": "16:9",
        },
        "instagram": {
            "max_length": 2200,
            "max_hashtags": 30,
            "image_ratio": "1:1",
        },
    }

    # 최적 포스팅 시간대 (KST 기준)
    OPTIMAL_HOURS = {
        "twitter": [7, 12, 18, 21],
        "instagram": [8, 12, 17, 20],
    }

    # 핵심 정책 주제
    CORE_TOPICS = [
        "AI 투명성과 정치 혁신",
        "시민 참여형 정책 결정",
        "디지털 민주주의",
        "청년 정치 참여",
        "공정한 경제 정책",
        "교육 혁신",
        "기후 변화 대응",
        "소수자 권리 보호",
        "주거 안정 정책",
        "노동 환경 개선",
    ]

    def __init__(self):
        """초기화: Claude API 연결 및 데이터 디렉토리 설정"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "").strip())
        self.party_name = os.getenv("PARTY_NAME", "민주AI")

        # 데이터 디렉토리
        base_dir = Path(__file__).parent.parent
        self.output_dir = base_dir / "data" / "outputs" / "marketing"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 포스트 저장소
        self.posts: List[Dict[str, Any]] = []
        self.scheduled_posts: List[Dict[str, Any]] = []
        self.performance_data: List[Dict[str, Any]] = []

        # 오늘 생성된 포스트 수
        self.daily_post_count = 0
        self.daily_target = random.randint(3, 5)

        # 해시태그 캐시: {content_hash: {"tags": [...], "expires_at": datetime}}
        self._hashtag_cache: Dict[str, Dict[str, Any]] = {}
        self._hashtag_cache_hits = 0
        self._hashtag_cache_misses = 0
        self.HASHTAG_CACHE_TTL_HOURS = 12  # 해시태그는 12시간 캐시

        logger.info(f"📱 마케팅 에이전트 초기화 완료 (오늘 목표: {self.daily_target}개, 해시태그 캐시 ON)")

    async def generate_daily_content(self) -> List[Dict[str, Any]]:
        """
        오늘의 SNS 콘텐츠 자동 생성

        Returns:
            생성된 포스트 목록
        """
        logger.info(f"📝 일일 콘텐츠 생성 시작 (목표: {self.daily_target}개)")

        today_posts = []
        self.daily_post_count = 0
        self.daily_target = random.randint(3, 5)

        # 오늘의 주제 선정
        topics = random.sample(self.CORE_TOPICS, min(self.daily_target, len(self.CORE_TOPICS)))

        # 플랫폼 배분: 트위터 다수, 인스타 일부
        platforms = []
        for i in range(self.daily_target):
            if i < self.daily_target - 1:
                platforms.append("twitter" if i % 2 == 0 else "instagram")
            else:
                platforms.append("instagram")

        for i, (topic, platform) in enumerate(zip(topics, platforms)):
            try:
                post = await self.create_post(topic, platform)
                if post:
                    today_posts.append(post)
                    self.daily_post_count += 1
                    logger.info(
                        f"  ✅ [{i+1}/{self.daily_target}] {platform} 포스트 생성 완료"
                    )
            except Exception as e:
                logger.error(f"  ❌ [{i+1}/{self.daily_target}] 포스트 생성 실패: {e}")

        # 스케줄링
        if today_posts:
            await self.schedule_posts(today_posts)

        # 일일 리포트 저장
        self._save_daily_report(today_posts)

        logger.info(
            f"📊 일일 콘텐츠 생성 완료: {self.daily_post_count}/{self.daily_target}개 성공"
        )
        return today_posts

    async def create_post(
        self, topic: str, platform: str, max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        특정 주제와 플랫폼에 맞는 포스트 작성 (재시도 로직 포함)

        Args:
            topic: 포스트 주제
            platform: 플랫폼 ('twitter' 또는 'instagram')
            max_retries: 최대 재시도 횟수

        Returns:
            생성된 포스트 딕셔너리 또는 None
        """
        if platform not in self.PLATFORM_LIMITS:
            logger.error(f"지원하지 않는 플랫폼: {platform}")
            return None

        limits = self.PLATFORM_LIMITS[platform]

        # 플랫폼별 시스템 프롬프트
        system_prompts = {
            "twitter": f"""당신은 '{self.party_name}' 정당의 SNS 마케팅 전문가입니다.
트위터 포스트를 작성하세요.

규칙:
- 반드시 {limits['max_length']}자 이내
- 간결하고 임팩트 있는 메시지
- 시민들의 공감을 이끌어내는 톤
- 해시태그는 별도로 제공됩니다 (본문에 포함하지 마세요)
- 이모지 적절히 사용 (1-2개)
- 정치적으로 중립적이고 건설적인 내용

JSON 형식으로 응답하세요:
{{"content": "포스트 본문", "tone": "informative|engaging|urgent|hopeful", "target_audience": "대상 설명"}}""",
            "instagram": f"""당신은 '{self.party_name}' 정당의 SNS 마케팅 전문가입니다.
인스타그램 캡션을 작성하세요.

규칙:
- {limits['max_length']}자 이내
- 스토리텔링 형식 권장
- 첫 줄이 가장 중요 (미리보기에 노출)
- 시민들의 참여를 유도하는 질문 포함
- 해시태그는 별도로 제공됩니다 (본문에 포함하지 마세요)
- 이모지 적극 활용 (3-5개)
- 줄바꿈으로 가독성 확보

JSON 형식으로 응답하세요:
{{"content": "캡션 본문", "tone": "informative|engaging|urgent|hopeful", "target_audience": "대상 설명", "image_suggestion": "이미지 제안"}}""",
        }

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=1000,
                    messages=[
                        {"role": "system", "content": system_prompts[platform]},
                        {"role": "user", "content": f"주제: {topic}\n\n날짜: {datetime.now().strftime('%Y년 %m월 %d일')}\n\n위 주제로 포스트를 작성해주세요."},
                    ],
                )

                raw_text = response.choices[0].message.content

                # JSON 파싱
                post_data = self._parse_json_response(raw_text)
                if not post_data or "content" not in post_data:
                    logger.warning(f"[시도 {attempt}/{max_retries}] Claude 응답 파싱 실패, 원본 텍스트 사용")
                    # 코드블록 마크다운 잔여물 제거 후 원본 사용
                    cleaned = self._clean_raw_text(raw_text)
                    post_data = {"content": cleaned, "tone": "informative", "target_audience": "일반 시민"}

                # 글자 수 제한 확인 및 자르기
                content = post_data["content"]
                if len(content) > limits["max_length"]:
                    content = content[: limits["max_length"] - 3] + "..."
                    post_data["content"] = content

                # 해시태그 최적화
                hashtags = await self.optimize_hashtags(content, platform)

                # 포스트 객체 생성
                post = {
                    "id": f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100, 999)}",
                    "platform": platform,
                    "topic": topic,
                    "content": post_data["content"],
                    "hashtags": hashtags,
                    "tone": post_data.get("tone", "informative"),
                    "target_audience": post_data.get("target_audience", "일반 시민"),
                    "image_suggestion": post_data.get("image_suggestion"),
                    "created_at": datetime.now().isoformat(),
                    "status": "draft",
                    "performance": {
                        "likes": 0,
                        "shares": 0,
                        "comments": 0,
                        "impressions": 0,
                    },
                }

                self.posts.append(post)
                return post

            except Exception as e:
                last_error = e
                logger.warning(f"[시도 {attempt}/{max_retries}] 포스트 생성 중 오류: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1)

        logger.error(f"포스트 생성 최종 실패 ({max_retries}회 시도): {last_error}")
        return None

    def _hashtag_cache_key(self, content: str, platform: str) -> str:
        """콘텐츠 해시로 캐시 키 생성 (앞 200자 기준)"""
        normalized = f"{platform}:{content[:200].strip().lower()}"
        return hashlib.md5(normalized.encode()).hexdigest()

    async def optimize_hashtags(
        self, content: str, platform: str = "twitter"
    ) -> List[str]:
        """
        콘텐츠에 맞는 최적 해시태그 생성 (캐시 우선)

        Args:
            content: 포스트 본문
            platform: 플랫폼명

        Returns:
            해시태그 리스트
        """
        limits = self.PLATFORM_LIMITS.get(platform, self.PLATFORM_LIMITS["twitter"])
        max_tags = min(limits["max_hashtags"], 10)

        # 기본 해시태그 (항상 포함)
        base_tags = [f"#{self.party_name}", "#AI정치", "#디지털민주주의"]

        # 캐시 확인
        cache_key = self._hashtag_cache_key(content, platform)
        cached = self._hashtag_cache.get(cache_key)
        if cached and datetime.now() < cached["expires_at"]:
            self._hashtag_cache_hits += 1
            logger.debug(f"#️⃣ 해시태그 캐시 HIT (총 {self._hashtag_cache_hits}회)")
            return cached["tags"]
        self._hashtag_cache_misses += 1

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=300,
                messages=[
                    {"role": "system", "content": f"""SNS 해시태그 전문가입니다.
주어진 콘텐츠에 최적화된 한국어 해시태그를 생성하세요.

규칙:
- 최대 {max_tags - len(base_tags)}개 추가 해시태그
- 트렌딩 가능성이 높은 태그 우선
- 정치/사회 관련 태그
- JSON 배열 형식으로만 응답: ["#태그1", "#태그2", ...]"""},
                    {"role": "user", "content": f"콘텐츠: {content[:200]}"},
                ],
            )

            raw = response.choices[0].message.content
            extra_tags = self._parse_json_response(raw)
            if isinstance(extra_tags, list):
                extra_tags = [
                    tag if tag.startswith("#") else f"#{tag}" for tag in extra_tags
                ]
                result_tags = base_tags + extra_tags[:max_tags - len(base_tags)]

                # 캐시 저장
                self._hashtag_cache[cache_key] = {
                    "tags": result_tags,
                    "expires_at": datetime.now() + timedelta(hours=self.HASHTAG_CACHE_TTL_HOURS),
                }
                # 캐시 크기 제한 (100개)
                if len(self._hashtag_cache) > 100:
                    oldest = min(self._hashtag_cache, key=lambda k: self._hashtag_cache[k]["expires_at"])
                    del self._hashtag_cache[oldest]

                return result_tags

        except Exception as e:
            logger.warning(f"해시태그 최적화 실패, 기본 태그 사용: {e}")

        return base_tags

    def get_hashtag_cache_stats(self) -> Dict[str, Any]:
        """해시태그 캐시 통계"""
        total = self._hashtag_cache_hits + self._hashtag_cache_misses
        return {
            "cache_size": len(self._hashtag_cache),
            "hits": self._hashtag_cache_hits,
            "misses": self._hashtag_cache_misses,
            "hit_rate": round(self._hashtag_cache_hits / max(total, 1) * 100, 1),
        }

    async def schedule_posts(
        self, posts: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        포스트를 최적 시간에 예약

        Args:
            posts: 예약할 포스트 목록 (None이면 드래프트 상태의 모든 포스트)

        Returns:
            스케줄된 포스트 목록
        """
        if posts is None:
            posts = [p for p in self.posts if p["status"] == "draft"]

        if not posts:
            logger.info("예약할 포스트가 없습니다")
            return []

        scheduled = []
        now = datetime.now()

        for post in posts:
            platform = post["platform"]
            optimal_hours = self.OPTIMAL_HOURS.get(platform, [9, 12, 18])

            # 아직 지나지 않은 최적 시간 중 하나 선택
            future_hours = [h for h in optimal_hours if h > now.hour]
            if not future_hours:
                # 내일의 첫 번째 최적 시간으로 예약
                scheduled_time = now.replace(
                    hour=optimal_hours[0], minute=0, second=0
                ) + timedelta(days=1)
            else:
                scheduled_time = now.replace(
                    hour=future_hours[0], minute=random.randint(0, 30), second=0
                )

            post["scheduled_at"] = scheduled_time.isoformat()
            post["status"] = "scheduled"
            scheduled.append(post)

            logger.info(
                f"  📅 [{post['platform']}] {scheduled_time.strftime('%H:%M')}에 예약됨"
            )

        self.scheduled_posts.extend(scheduled)

        # 스케줄 저장
        schedule_file = self.output_dir / f"schedule_{now.strftime('%Y%m%d')}.json"
        with open(schedule_file, "w", encoding="utf-8") as f:
            json.dump(scheduled, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ {len(scheduled)}개 포스트 스케줄링 완료")
        return scheduled

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        마케팅 성과 통계 반환

        Returns:
            성과 통계 딕셔너리
        """
        total_posts = len(self.posts)
        published = [p for p in self.posts if p["status"] == "published"]
        scheduled = [p for p in self.posts if p["status"] == "scheduled"]

        # 플랫폼별 통계
        platform_stats = {}
        for platform in self.PLATFORM_LIMITS:
            platform_posts = [p for p in self.posts if p["platform"] == platform]
            platform_published = [p for p in platform_posts if p["status"] == "published"]

            total_likes = sum(
                p["performance"]["likes"] for p in platform_published
            )
            total_shares = sum(
                p["performance"]["shares"] for p in platform_published
            )
            total_comments = sum(
                p["performance"]["comments"] for p in platform_published
            )
            total_impressions = sum(
                p["performance"]["impressions"] for p in platform_published
            )

            platform_stats[platform] = {
                "total_posts": len(platform_posts),
                "published": len(platform_published),
                "total_likes": total_likes,
                "total_shares": total_shares,
                "total_comments": total_comments,
                "total_impressions": total_impressions,
                "engagement_rate": (
                    round(
                        (total_likes + total_shares + total_comments)
                        / max(total_impressions, 1)
                        * 100,
                        2,
                    )
                ),
            }

        # 톤별 분석
        tone_distribution = {}
        for post in self.posts:
            tone = post.get("tone", "unknown")
            tone_distribution[tone] = tone_distribution.get(tone, 0) + 1

        stats = {
            "summary": {
                "total_posts": total_posts,
                "published": len(published),
                "scheduled": len(scheduled),
                "drafts": total_posts - len(published) - len(scheduled),
                "daily_target": self.daily_target,
                "daily_completed": self.daily_post_count,
            },
            "platforms": platform_stats,
            "tone_distribution": tone_distribution,
            "generated_at": datetime.now().isoformat(),
        }

        return stats

    def get_marketing_report(self) -> str:
        """
        마케팅 성과 리포트를 마크다운 형식으로 생성

        Returns:
            마크다운 리포트 문자열
        """
        stats = self.get_performance_stats()
        now = datetime.now()

        report = f"""# 📱 마케팅 에이전트 일일 리포트
**생성일시**: {now.strftime('%Y년 %m월 %d일 %H:%M')}

## 요약
- 총 포스트: {stats['summary']['total_posts']}개
- 발행 완료: {stats['summary']['published']}개
- 예약 대기: {stats['summary']['scheduled']}개
- 오늘 목표: {stats['summary']['daily_target']}개 / 달성: {stats['summary']['daily_completed']}개

## 플랫폼별 성과
"""
        for platform, pstats in stats["platforms"].items():
            report += f"""
### {platform.upper()}
| 항목 | 수치 |
|------|------|
| 총 포스트 | {pstats['total_posts']}개 |
| 좋아요 | {pstats['total_likes']} |
| 공유 | {pstats['total_shares']} |
| 댓글 | {pstats['total_comments']} |
| 노출수 | {pstats['total_impressions']} |
| 참여율 | {pstats['engagement_rate']}% |
"""

        report += f"""
## 콘텐츠 톤 분포
"""
        for tone, count in stats["tone_distribution"].items():
            report += f"- {tone}: {count}개\n"

        return report

    def _clean_raw_text(self, text: str) -> str:
        """응답 텍스트에서 마크다운 코드블록 잔여물 제거"""
        cleaned = text.strip()
        # ```json ... ``` 또는 ``` ... ``` 래퍼 제거
        if cleaned.startswith("```"):
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            else:
                cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _parse_json_response(self, text: str) -> Any:
        """Claude 응답에서 JSON 파싱 (안전한 find 기반)"""
        # 직접 파싱 시도
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # ```json 코드 블록 추출
        json_fence = text.find("```json")
        if json_fence != -1:
            start = json_fence + 7
            end = text.find("```", start)
            if end != -1:
                try:
                    return json.loads(text[start:end].strip())
                except (json.JSONDecodeError, ValueError):
                    pass

        # 일반 ``` 코드 블록 추출
        fence = text.find("```")
        if fence != -1:
            start = fence + 3
            # 첫 줄이 언어 태그일 수 있으므로 줄바꿈 이후부터 파싱
            newline = text.find("\n", start)
            if newline != -1:
                start = newline + 1
            end = text.find("```", start)
            if end != -1:
                try:
                    return json.loads(text[start:end].strip())
                except (json.JSONDecodeError, ValueError):
                    pass

        # { } 또는 [ ] 패턴 추출
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            s = text.find(start_char)
            e = text.rfind(end_char)
            if s != -1 and e != -1 and e > s:
                try:
                    return json.loads(text[s:e + 1])
                except (json.JSONDecodeError, ValueError):
                    pass

        return None

    def _save_daily_report(self, posts: List[Dict[str, Any]]):
        """일일 리포트 파일 저장"""
        report_file = (
            self.output_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        )

        report_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "target": self.daily_target,
            "generated": len(posts),
            "posts": posts,
            "stats": self.get_performance_stats(),
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 일일 리포트 저장: {report_file}")


async def main():
    """마케팅 에이전트 테스트 실행"""
    agent = MarketingAgent()

    # 1. 일일 콘텐츠 생성
    logger.info("=== 일일 콘텐츠 생성 테스트 ===")
    posts = await agent.generate_daily_content()

    for post in posts:
        logger.info(f"\n--- {post['platform'].upper()} ---")
        logger.info(f"주제: {post['topic']}")
        logger.info(f"내용: {post['content'][:100]}...")
        logger.info(f"해시태그: {' '.join(post['hashtags'])}")
        logger.info(f"톤: {post['tone']}")
        logger.info(f"예약: {post.get('scheduled_at', 'N/A')}")

    # 2. 성과 통계
    logger.info("\n=== 성과 통계 ===")
    stats = agent.get_performance_stats()
    logger.info(json.dumps(stats, indent=2, ensure_ascii=False))

    # 3. 마크다운 리포트
    report = agent.get_marketing_report()
    logger.info(f"\n{report}")


if __name__ == "__main__":
    asyncio.run(main())
