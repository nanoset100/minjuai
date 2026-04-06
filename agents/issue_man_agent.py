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

# ─── 광역 단위 약칭 매핑 (1차 빠른 필터용) ──────────────────────────────
REGION_ABBREV = {
    "서울": "서울", "부산": "부산", "인천": "인천", "대구": "대구",
    "광주": "광주", "대전": "대전", "울산": "울산", "세종": "세종",
    "경기": "경기", "강원": "강원", "충북": "충북", "충남": "충남",
    "전북": "전북", "전남": "전남", "경북": "경북", "경남": "경남",
    "제주": "제주",
}


def build_district_index(lawmakers_path: Path) -> Dict[str, List[Dict]]:
    """
    실제 의원 데이터에서 지역구 역인덱스 생성
    반환: { "해운대": [{"district": "부산 해운대구을", "mona_cd": "3BC6890E"}, ...], ... }
    """
    import re
    index: Dict[str, List[Dict]] = {}

    try:
        with open(lawmakers_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.warning(f"의원 데이터 로드 실패: {e}")
        return index

    for m in data:
        district = m.get("district", "")
        mona_cd = m.get("mona_cd", "")
        if not district or district == "비례대표" or not mona_cd:
            continue

        entry = {"district": district, "mona_cd": mona_cd}

        # 광역 단위 (서울, 부산, 경기 등)
        parts = district.split(" ", 1)
        region = parts[0]
        for abbrev in REGION_ABBREV:
            if district.startswith(abbrev):
                index.setdefault(abbrev, []).append(entry)

        # 세부 지역 키워드 추출 (시/구/군 단위)
        sub = parts[1] if len(parts) > 1 else district
        sub_clean = re.sub(r"[갑을병정]$", "", sub)  # 갑/을/병/정 제거

        # 예: "해운대구" → "해운대", "성남시분당구" → "성남", "분당"
        tokens = re.findall(r"([가-힣]+?)(?:특별자치시|특별시|광역시|자치시|시|구|군)", sub_clean)
        for token in tokens:
            if len(token) >= 2:  # 1글자 단위(동/서/남/북)는 애매해서 제외
                index.setdefault(token, []).append(entry)

    logger.info(f"📍 지역구 인덱스 구축: {len(index)}개 키워드 → {sum(len(v) for v in index.values())}개 매핑")
    return index

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

        # 실제 의원 데이터 기반 지역구 인덱스 로드
        lawmakers_path = Path(__file__).parent.parent / "data" / "assembly" / "lawmakers_real.json"
        self._district_index = build_district_index(lawmakers_path)

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

        # 1차: 실제 지역구 인덱스로 후보 추출
        combined = f"{article['title']} {article['description']}"
        matched_districts: Dict[str, str] = {}  # district → mona_cd

        for keyword, entries in self._district_index.items():
            if keyword in combined:
                for entry in entries:
                    matched_districts[entry["district"]] = entry["mona_cd"]

        # 지역 관련 없는 기사는 '전국' 이슈로 처리
        if matched_districts:
            candidates_str = ", ".join(list(matched_districts.keys())[:5])
            region_context = f"매칭된 지역구 후보: {candidates_str}"
        else:
            region_context = "지역 특정 어려움 (전국 이슈)"

        # 후보 지역구 목록을 AI에게 제공 (없으면 전국)
        candidate_list = list(matched_districts.keys())[:5] if matched_districts else []

        prompt = f"""다음 뉴스 기사를 시민제보 형식으로 변환해주세요.

기사 제목: {article['title']}
기사 내용: {article['description']}
출처: {article['source']}
{region_context}

다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{{
  "relevant": true/false,
  "district": "{candidate_list[0] if candidate_list else '전국'}",
  "report_type": "현안" 또는 "기사",
  "title": "시민제보 제목 (30자 이내)",
  "content": "시민제보 내용 (100-200자, 문제점과 필요한 조치 중심)",
  "policy_suggestion": "정책 제안 한 줄 (없으면 null)"
}}

district는 반드시 후보 목록 중 가장 관련 높은 것을 선택하세요: {candidate_list if candidate_list else ['전국']}"""

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
            # 지역구 인덱스에서 mona_cd 즉시 조회 (DB 추가 호출 없음)
            mona_cd = self._get_mona_cd(report["district"])

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

    def _get_mona_cd(self, district: str) -> str:
        """지역구 인덱스에서 mona_cd 조회 (DB 호출 없음, 빠름)"""
        if district == "전국":
            return "NATIONAL"

        # 정확히 매칭되는 지역구 먼저 탐색
        for keyword, entries in self._district_index.items():
            for entry in entries:
                if entry["district"] == district:
                    return entry["mona_cd"]

        # 부분 매칭 (예: "서울 강남구"로 "서울 강남구병" 매칭)
        for keyword, entries in self._district_index.items():
            if keyword in district or district in keyword:
                if entries:
                    return entries[0]["mona_cd"]

        return "NATIONAL"

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
