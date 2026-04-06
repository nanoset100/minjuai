#!/usr/bin/env python3
"""
이슈맨 AI - 뉴스 자동 수집 및 지역구 시민제보 등록 에이전트

동작:
1. 주요 한국 뉴스 RSS 피드 수집 (연합뉴스, 뉴스1, 한겨레 등)
2. GPT-4o mini로 정치/사회 이슈 필터링 및 지역구 매핑
3. district_reports 테이블에 자동 등록 (user_name='이슈맨AI')

실행 주기: 하루 2회 (오전 8시, 오후 6시)
비용 최적화: RSS 필터링 후 관련 기사만 AI 처리
"""

import os
import sys
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

import aiohttp
import feedparser
from openai import AsyncOpenAI
from dotenv import load_dotenv
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(Path(__file__).parent.parent / "config" / ".env")


# ─── 뉴스 RSS 소스 ───────────────────────────────────────────────────
RSS_SOURCES = [
    {
        "name": "연합뉴스_정치",
        "url": "https://www.yna.co.kr/rss/politics.xml",
    },
    {
        "name": "연합뉴스_사회",
        "url": "https://www.yna.co.kr/rss/society.xml",
    },
    {
        "name": "연합뉴스_지역",
        "url": "https://www.yna.co.kr/rss/local.xml",
    },
    {
        "name": "뉴스1_정치",
        "url": "https://www.news1.kr/rss/politics",
    },
    {
        "name": "뉴스1_사회",
        "url": "https://www.news1.kr/rss/society",
    },
    {
        "name": "한겨레_정치",
        "url": "https://www.hani.co.kr/rss/politics/",
    },
    {
        "name": "KBS_정치",
        "url": "https://world.kbs.co.kr/rss/rss_news.htm?lang=k",
    },
]

# ─── 지역구 키워드 매핑 (빠른 1차 필터) ───────────────────────────────
DISTRICT_KEYWORDS = {
    "서울특별시": ["서울", "종로", "중구", "용산", "성동", "광진", "동대문", "중랑", "성북", "강북",
                  "도봉", "노원", "은평", "서대문", "마포", "양천", "강서", "구로", "금천",
                  "영등포", "동작", "관악", "서초", "강남", "송파", "강동"],
    "부산광역시": ["부산", "해운대", "수영", "남구", "북구", "사하", "사상", "금정", "동래", "연제"],
    "인천광역시": ["인천", "남동", "연수", "미추홀", "부평", "계양", "서구"],
    "대구광역시": ["대구", "달서", "달성", "수성", "북구", "동구"],
    "광주광역시": ["광주", "서구", "북구", "남구", "동구"],
    "대전광역시": ["대전", "서구", "유성", "대덕", "동구"],
    "울산광역시": ["울산", "남구", "북구", "동구", "중구"],
    "경기도": ["경기", "수원", "성남", "고양", "용인", "부천", "안산", "남양주", "화성", "안양",
               "평택", "의정부", "파주", "시흥", "김포", "광명", "광주", "하남", "오산"],
    "경상남도": ["경남", "창원", "김해", "진주", "양산", "통영", "거제"],
    "경상북도": ["경북", "포항", "구미", "경주", "안동", "칠곡"],
    "전라남도": ["전남", "순천", "여수", "목포", "광양"],
    "전라북도": ["전북", "전주", "익산", "군산", "정읍"],
    "충청남도": ["충남", "천안", "아산", "당진", "서산"],
    "충청북도": ["충북", "청주", "충주", "제천"],
    "강원도": ["강원", "춘천", "원주", "강릉", "속초"],
    "제주특별자치도": ["제주", "서귀포"],
    "세종특별자치시": ["세종"],
}

# 정치/사회 관련 키워드 (1차 필터)
RELEVANT_KEYWORDS = [
    "국회", "의원", "정부", "장관", "대통령", "여당", "야당",
    "정책", "법안", "예산", "지원", "복지", "의료", "교육",
    "환경", "교통", "주택", "청년", "노인", "장애", "취약계층",
    "부패", "비리", "감사", "시위", "민원", "갈등",
    "경제", "일자리", "물가", "금리", "부동산",
    "안전", "사고", "재난", "범죄",
]


class IssueManAgent:
    """
    이슈맨 AI 에이전트

    뉴스 RSS에서 정치/사회 이슈를 자동 수집하여
    지역구별 시민제보로 변환 후 DB에 등록한다.
    """

    MAX_ARTICLES_PER_RUN = 30    # 1회 실행 최대 처리 기사 수 (비용 관리)
    DEDUP_WINDOW_HOURS = 48      # 중복 제거 기간 (시간)

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "").strip())
        self.model = "gpt-4o-mini"
        self._processed_hashes: set = set()  # 중복 방지 (런타임)

        logger.info("🗞️ 이슈맨 AI 초기화 완료")

    # ─── RSS 수집 ───────────────────────────────────────────────────

    async def fetch_rss(self, session: aiohttp.ClientSession, source: Dict) -> List[Dict]:
        """단일 RSS 피드 수집 (feedparser 사용)"""
        articles = []
        try:
            async with session.get(
                source["url"],
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"User-Agent": "Mozilla/5.0 (compatible; IssueManBot/1.0)"},
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"RSS 수집 실패: {source['name']} (HTTP {resp.status})")
                    return []
                content = await resp.read()

            # feedparser로 파싱 (인코딩 자동 감지)
            feed = feedparser.parse(content)

            for entry in feed.entries[:15]:  # 최신 15개만
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                summary = summary.strip()[:300]

                if not title or not link:
                    continue

                # 1차 필터: 관련 키워드 포함 여부
                combined = f"{title} {summary}"
                if not any(kw in combined for kw in RELEVANT_KEYWORDS):
                    continue

                articles.append({
                    "source": source["name"],
                    "title": title,
                    "url": link,
                    "description": summary,
                    "pub_date": getattr(entry, "published", ""),
                })

        except Exception as e:
            logger.warning(f"RSS 오류: {source['name']} - {e}")

        return articles

    async def collect_all_rss(self) -> List[Dict]:
        """모든 RSS 소스에서 병렬 수집"""
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_rss(session, src) for src in RSS_SOURCES]
            results = await asyncio.gather(*tasks)

        articles = []
        seen_titles = set()
        for batch in results:
            for article in batch:
                # 제목 기반 중복 제거
                title_hash = hashlib.md5(article["title"].encode()).hexdigest()
                if title_hash not in seen_titles and title_hash not in self._processed_hashes:
                    seen_titles.add(title_hash)
                    articles.append(article)

        logger.info(f"📰 RSS 수집 완료: {len(articles)}개 기사 (필터링 후)")
        return articles[:self.MAX_ARTICLES_PER_RUN]

    # ─── AI 분석 ────────────────────────────────────────────────────

    async def analyze_article(self, article: Dict) -> Optional[Dict]:
        """
        GPT-4o mini로 기사 분석:
        - 지역구 추출
        - 이슈 타입 분류 (현안/기사)
        - 시민제보 형식으로 변환
        """

        # 1차: 지역 키워드로 빠른 지역구 후보 추출
        combined = f"{article['title']} {article['description']}"
        region_candidates = []
        for region, keywords in DISTRICT_KEYWORDS.items():
            if any(kw in combined for kw in keywords):
                region_candidates.append(region)

        # 지역 관련 없는 기사는 '전국' 이슈로 처리
        region_context = (
            f"관련 지역 후보: {', '.join(region_candidates)}"
            if region_candidates
            else "지역 특정 어려움 (전국 이슈)"
        )

        prompt = f"""다음 뉴스 기사를 시민제보 형식으로 변환해주세요.

기사 제목: {article['title']}
기사 내용: {article['description']}
출처: {article['source']}
{region_context}

다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{{
  "relevant": true/false,  // 정치/사회/민생 관련 여부
  "district": "지역구명 또는 '전국'",  // 예: "서울특별시", "부산광역시", "전국"
  "report_type": "현안" 또는 "기사",  // 현안=시민이 직접 겪는 문제, 기사=뉴스 보도
  "title": "시민제보 제목 (30자 이내, 핵심 이슈 중심)",
  "content": "시민제보 내용 (100-200자, 문제점과 필요한 조치 중심으로)",
  "policy_suggestion": "정책 제안 한 줄 (없으면 null)"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=400,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "당신은 뉴스를 시민 참여형 정치 플랫폼의 제보 데이터로 변환하는 AI입니다. "
                            "반드시 JSON만 출력하세요."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            text = response.choices[0].message.content.strip()
            # JSON 파싱
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            result = json.loads(text.strip())

            if not result.get("relevant", False):
                return None

            return {
                **result,
                "news_url": article["url"],
                "source_name": article["source"],
                "original_title": article["title"],
            }

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"AI 분석 파싱 실패: {article['title'][:30]} - {e}")
            return None
        except Exception as e:
            logger.error(f"AI 분석 오류: {e}")
            return None

    # ─── DB 등록 ─────────────────────────────────────────────────────

    async def save_to_db(self, db, report: Dict) -> bool:
        """district_reports 테이블에 저장"""
        try:
            # 지역구 → 의원 mona_cd 매핑 (없으면 지역 대표값 사용)
            mona_cd = await self._get_mona_cd(db, report["district"])

            data = {
                "district": report["district"],
                "mona_cd": mona_cd,
                "report_type": report["report_type"],
                "title": report["title"],
                "content": report["content"],
                "news_url": report.get("news_url"),
                "user_name": "이슈맨AI",
                "status": "published",
            }

            result = db.table("district_reports").insert(data).execute()
            if result.data:
                logger.info(f"✅ 등록: [{report['district']}] {report['title'][:30]}")
                return True
        except Exception as e:
            logger.error(f"DB 저장 실패: {e}")
        return False

    async def _get_mona_cd(self, db, district: str) -> str:
        """지역구에서 대표 의원 mona_cd 조회"""
        try:
            result = (
                db.table("assembly_members")
                .select("mona_cd")
                .ilike("district", f"%{district.replace('특별시','').replace('광역시','').replace('도','').strip()}%")
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]["mona_cd"]
        except Exception:
            pass
        return "NATIONAL"  # 전국 이슈 기본값

    # ─── 메인 실행 ───────────────────────────────────────────────────

    async def run(self, db) -> Dict[str, Any]:
        """이슈맨 AI 1회 실행"""
        start_time = datetime.now()
        logger.info(f"🚀 이슈맨 AI 실행 시작: {start_time.strftime('%Y-%m-%d %H:%M')}")

        # 1. RSS 수집
        articles = await self.collect_all_rss()
        if not articles:
            logger.warning("수집된 기사 없음")
            return {"collected": 0, "registered": 0}

        # 2. AI 분석 (병렬 처리, 최대 10개씩 배치)
        registered = 0
        skipped = 0
        batch_size = 10

        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            tasks = [self.analyze_article(article) for article in batch]
            results = await asyncio.gather(*tasks)

            for article, report in zip(batch, results):
                if report is None:
                    skipped += 1
                    continue

                # DB 저장
                success = await self.save_to_db(db, report)
                if success:
                    registered += 1
                    # 처리된 기사 해시 등록 (중복 방지)
                    title_hash = hashlib.md5(article["title"].encode()).hexdigest()
                    self._processed_hashes.add(title_hash)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"✅ 이슈맨 완료: 수집 {len(articles)}개 → 등록 {registered}개 "
            f"(스킵 {skipped}개) / {elapsed:.1f}초"
        )

        return {
            "collected": len(articles),
            "registered": registered,
            "skipped": skipped,
            "elapsed_seconds": round(elapsed, 1),
        }

    def get_stats(self) -> Dict[str, Any]:
        """실행 통계"""
        return {
            "processed_hashes": len(self._processed_hashes),
            "rss_sources": len(RSS_SOURCES),
            "max_per_run": self.MAX_ARTICLES_PER_RUN,
        }


# ─── 독립 실행 테스트 ─────────────────────────────────────────────────

async def test_issue_man():
    """로컬 테스트 (DB 없이 RSS + AI 분석만)"""
    agent = IssueManAgent()

    logger.info("📰 RSS 수집 테스트...")
    articles = await agent.collect_all_rss()
    logger.info(f"수집: {len(articles)}개")

    if articles:
        logger.info("\n🤖 첫 번째 기사 AI 분석 테스트...")
        report = await agent.analyze_article(articles[0])
        if report:
            logger.info(f"결과: {json.dumps(report, ensure_ascii=False, indent=2)}")
        else:
            logger.info("해당 기사는 필터링됨")

        # 추가 5개 미리보기
        logger.info("\n📋 수집된 기사 목록 (상위 5개):")
        for a in articles[:5]:
            logger.info(f"  [{a['source']}] {a['title'][:50]}")


if __name__ == "__main__":
    asyncio.run(test_issue_man())
