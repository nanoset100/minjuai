"""
reaction_pipeline.py
이슈 × 의원 반응 배치 파이프라인 (매일 새벽 2시 실행)

흐름:
  1. Supabase에서 활성 이슈 목록 조회
  2. 각 이슈의 키워드 + 의원명 → 네이버 뉴스 검색
  3. GPT-4o mini로 찬성/반대/침묵 분류 (confidence >= 0.7)
  4. Supabase issue_reactions에 저장

조회 시 GPT 호출 절대 금지 — 이 파이프라인만 GPT 호출

[2026-04-13] Assembly API 속기록 엔드포인트(nrypmbwncpfmvoecp) 미존재 확인.
             네이버 뉴스 검색 API로 대체 (의원명 + 이슈 키워드 조합 검색)
"""

import os
import json
import httpx
import re
import asyncio
from datetime import date, datetime
from typing import Optional
from openai import OpenAI

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# 네이버 뉴스 검색 API
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"

# 신뢰도 임계값 — 이 미만이면 "침묵"으로 처리
CONFIDENCE_THRESHOLD = 0.7

# GPT 프롬프트 (CLAUDE.md 지정)
STANCE_CLASSIFICATION_PROMPT = """
당신은 국회 발언 분석가입니다.

정책 이슈: {issue_title}
의원 발언 목록: {speeches}

분류 기준:
- "찬성": 긍정적 지지 발언이 명확한 경우
- "반대": 부정적 반대 발언이 명확한 경우
- "침묵": 관련 발언 없거나 중립적인 경우

반드시 JSON으로만 응답:
{{
  "stance": "찬성|반대|침묵",
  "confidence": 0.0~1.0,
  "summary": "한 줄 요약 30자 이내",
  "evidence": "근거 발언 원문 50자 이내 (없으면 null)"
}}

주의: 확실하지 않으면 침묵으로 분류. 과도한 추론 금지.
"""


class ReactionPipeline:
    def __init__(self):
        self.openai = OpenAI(api_key=OPENAI_API_KEY)
        self.headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
        }

    # ─── Supabase 헬퍼 ─────────────────────────────────────────

    def _sb_get(self, table: str, query: str = "") -> list:
        url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
        resp = httpx.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _sb_upsert(self, table: str, rows: list, on_conflict: str = "") -> None:
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        if on_conflict:
            url += f"?on_conflict={on_conflict}"
        headers = {**self.headers, "Prefer": "resolution=merge-duplicates,return=minimal"}
        resp = httpx.post(url, headers=headers, json=rows, timeout=30)
        if resp.status_code not in (200, 201):
            print(f"[Pipeline] Supabase upsert 오류 ({table}): {resp.text[:200]}")

    # ─── 네이버 뉴스 검색 ─────────────────────────────────────

    def fetch_speeches(self, member_name: str, keywords: list[str]) -> list[str]:
        """의원명 + 키워드로 네이버 뉴스 검색 → 발언/입장 텍스트 추출"""
        snippets = []
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        }

        for keyword in keywords[:3]:  # 키워드 최대 3개
            query = f"{member_name} {keyword}"
            params = {
                "query": query,
                "display": 5,
                "sort": "date",  # 최신순
            }
            try:
                resp = httpx.get(NAVER_NEWS_URL, headers=headers, params=params, timeout=15)
                resp.raise_for_status()
                items = resp.json().get("items", [])
                for item in items:
                    # HTML 태그 제거
                    title = re.sub(r"<[^>]+>", "", item.get("title", ""))
                    desc = re.sub(r"<[^>]+>", "", item.get("description", ""))
                    text = f"{title}. {desc}".strip()
                    if len(text) > 20:
                        snippets.append(text[:300])
            except Exception as e:
                print(f"[Pipeline] 뉴스 검색 오류 ({query}): {e}")

        return snippets[:5]  # 최대 5개

    # ─── GPT 분류 ─────────────────────────────────────────────

    def classify_stance(self, issue_title: str, speeches: list[str]) -> dict:
        """GPT로 찬반 분류. confidence < CONFIDENCE_THRESHOLD면 침묵으로 강제"""
        if not speeches:
            return {
                "stance": "침묵",
                "confidence": 1.0,
                "summary": "관련 발언 없음",
                "evidence": None
            }

        speeches_text = "\n".join([f"- {s}" for s in speeches])
        prompt = STANCE_CLASSIFICATION_PROMPT.format(
            issue_title=issue_title,
            speeches=speeches_text
        )

        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=300,
            )
            raw = response.choices[0].message.content.strip()

            # JSON 파싱
            if "```" in raw:
                raw = raw.split("```")[1].replace("json", "").strip()
            result = json.loads(raw)

            # confidence 임계값 강제 적용 (code-level enforcement)
            if result.get("confidence", 0) < CONFIDENCE_THRESHOLD:
                result["stance"] = "침묵"
                result["summary"] = f"신뢰도 미달 ({result['confidence']:.2f} < {CONFIDENCE_THRESHOLD})"
                result["evidence"] = None

            # summary/evidence 길이 제한
            if result.get("summary"):
                result["summary"] = result["summary"][:30]
            if result.get("evidence"):
                result["evidence"] = result["evidence"][:50]

            return result

        except Exception as e:
            print(f"[Pipeline] GPT 분류 오류: {e}")
            return {
                "stance": "수집중",
                "confidence": 0.0,
                "summary": "분류 중 오류 발생",
                "evidence": None
            }

    # ─── 메인 파이프라인 ──────────────────────────────────────

    def run(self):
        """전체 파이프라인 실행 (매일 새벽 2시 Railway Cron에서 호출)"""
        today = date.today().isoformat()
        print(f"\n[Pipeline] 배치 시작: {today}")
        print("=" * 60)

        # 1. 활성 이슈 목록 조회
        issues = self._sb_get("issues", "?is_active=eq.true&order=collected_at.desc&limit=20")
        print(f"[Pipeline] 활성 이슈 {len(issues)}건")

        # 2. 광주 의원 목록 조회
        members = self._sb_get("members", "?city=eq.광주광역시&is_active=eq.true")
        print(f"[Pipeline] 광주 의원 {len(members)}명")

        if not issues or not members:
            print("[Pipeline] 이슈 또는 의원 없음 — 종료")
            return

        # 3. 이슈 × 의원 조합 처리
        total_processed = 0
        total_saved = 0

        for issue in issues:
            issue_id = issue["id"]
            issue_title = issue["title"]
            keywords = issue.get("keywords") or []
            print(f"\n[Issue] {issue_title[:40]}")

            for member in members:
                mona_cd = member["mona_cd"]
                name = member["name"]
                total_processed += 1

                # 뉴스 검색 (의원명 + 이슈 키워드)
                speeches = self.fetch_speeches(name, keywords)

                # GPT 분류
                result = self.classify_stance(issue_title, speeches)

                # Supabase 저장
                row = {
                    "issue_id": issue_id,
                    "member_id": mona_cd,
                    "stance": result["stance"],
                    "confidence": result.get("confidence"),
                    "summary": result.get("summary"),
                    "evidence": result.get("evidence"),
                    "data_date": today,
                }

                self._sb_upsert("issue_reactions", [row], on_conflict="issue_id,member_id,data_date")
                total_saved += 1

                stance_display = result["stance"]
                conf = result.get("confidence", 0)
                print(f"  {name}: {stance_display} (confidence={conf:.2f})")

        print(f"\n[Pipeline] 완료: {total_processed}건 처리, {total_saved}건 저장")
        print("=" * 60)


# 직접 실행 시 (테스트용)
if __name__ == "__main__":
    pipeline = ReactionPipeline()
    pipeline.run()
