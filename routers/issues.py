"""
routers/issues.py
이슈 × 의원 반응 API

GET /api/issues              — 활성 이슈 목록 (최신순)
GET /api/issues/{id}         — 이슈 상세 + 광주 의원 반응 목록
GET /api/members             — 광주 의원 목록
"""

import os
import httpx
from fastapi import APIRouter, HTTPException
from datetime import date, timedelta

router = APIRouter(prefix="/api", tags=["issues"])

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


def sb_get(table: str, query: str = "") -> list:
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    resp = httpx.get(f"{SUPABASE_URL}/rest/v1/{table}{query}", headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()


@router.get("/issues")
def list_issues(limit: int = 10):
    """활성 이슈 목록 — 배치 캐시 읽기만, GPT 호출 없음"""
    rows = sb_get("issues", f"?is_active=eq.true&order=collected_at.desc&limit={min(limit, 30)}")
    return {"issues": rows, "count": len(rows)}


@router.get("/issues/{issue_id}")
def get_issue_with_reactions(issue_id: str):
    """이슈 상세 + 광주 의원 반응"""
    # 이슈 조회
    issues = sb_get("issues", f"?id=eq.{issue_id}&limit=1")
    if not issues:
        raise HTTPException(status_code=404, detail="이슈를 찾을 수 없습니다")
    issue = issues[0]

    # 가장 최근 data_date 기준 반응 조회
    reactions = sb_get(
        "issue_reactions",
        f"?issue_id=eq.{issue_id}&order=data_date.desc&limit=50"
    )

    # 의원별 최신 반응만 (mona_cd 중복 제거)
    seen = set()
    latest_reactions = []
    for r in reactions:
        mid = r["member_id"]
        if mid not in seen:
            seen.add(mid)
            latest_reactions.append(r)

    # 의원 정보 조인
    members = sb_get("members", "?city=eq.광주광역시&is_active=eq.true")
    member_map = {m["mona_cd"]: m for m in members}

    enriched = []
    for r in latest_reactions:
        m = member_map.get(r["member_id"], {})
        enriched.append({
            **r,
            "member_name": m.get("name", ""),
            "member_party": m.get("party", ""),
            "member_district": m.get("district", ""),
            "member_photo": m.get("photo_url", ""),
        })

    # data_date 표시용 (신뢰도 명시 — 실시간 인상 금지)
    data_date = reactions[0]["data_date"] if reactions else None
    is_stale = False
    if data_date:
        days_old = (date.today() - date.fromisoformat(data_date)).days
        is_stale = days_old > 7

    return {
        "issue": issue,
        "reactions": enriched,
        "data_date": data_date,
        "is_stale": is_stale,
        "stale_message": "데이터 갱신 중" if is_stale else None,
    }


@router.get("/members")
def list_members(city: str = "광주광역시"):
    """광주 의원 목록"""
    rows = sb_get("members", f"?city=eq.{city}&is_active=eq.true&order=district.asc")
    return {"members": rows, "count": len(rows)}
