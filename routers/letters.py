"""
routers/letters.py
시민 → 의원 편지/문의 API

POST /api/letters                    — 편지/문의 제출 + SendGrid 발송
GET  /api/letters/stats              — 누적 발송 카운터 (홈 화면용)
GET  /api/members/{mona_cd}/reply-rate — 의원별 응답률
"""

import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/api", tags=["letters"])

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


class LetterRequest(BaseModel):
    mona_cd: str = Field(..., description="의원 코드 (Assembly API MONA_CD)")
    content: str = Field(..., min_length=10, description="편지/문의 내용")
    nickname: str = Field(default="시민", max_length=20)
    sender_district: str = Field(default="", max_length=30, description="시민 지역구 (예: 광주 북구갑)")
    issue_id: Optional[str] = Field(default=None, description="연관 이슈 UUID")
    letter_type: str = Field(default="letter", pattern="^(letter|inquiry)$", description="letter 또는 inquiry")
    citizen_email: Optional[str] = Field(default=None, max_length=100, description="답변 알림용 이메일 (선택)")


@router.post("/letters")
def submit_letter(req: LetterRequest):
    """편지/문의 제출 — 스팸 필터 → SendGrid 발송 → 결과 반환"""
    from services.letter_service import LetterService
    service = LetterService()

    result = service.submit_letter(
        mona_cd=req.mona_cd,
        content=req.content,
        nickname=req.nickname,
        sender_district=req.sender_district,
        issue_id=req.issue_id,
        letter_type=req.letter_type,
        citizen_email=req.citizen_email,
    )

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    if result.get("blocked"):
        raise HTTPException(
            status_code=422,
            detail={
                "blocked": True,
                "reason": result.get("reason", "발송 기준에 맞지 않습니다"),
            }
        )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail="발송 중 오류가 발생했습니다")

    type_label = "문의" if req.letter_type == "inquiry" else "편지"
    response = {
        "success": True,
        "letter_id": result["letter_id"],
        "member_name": result["member_name"],
        "sent_at": result["sent_at"],
        "total_sent": result["total_sent"],
        "message": f"{result['member_name']} 의원실에 {type_label}가 전달됐습니다",
    }
    if result.get("reply_rate_pct") is not None:
        response["reply_rate_pct"] = result["reply_rate_pct"]
    return response


@router.get("/members/{mona_cd}/reply-rate")
def get_reply_rate(mona_cd: str):
    """의원별 문의 응답률 조회"""
    from services.letter_service import LetterService
    service = LetterService()
    member = service.get_member(mona_cd)
    if not member:
        raise HTTPException(status_code=404, detail="의원 정보를 찾을 수 없습니다")
    rate = service.get_reply_rate(mona_cd)
    return {
        "mona_cd": mona_cd,
        "member_name": member["name"],
        "total_inquiries": rate.get("total_inquiries", 0),
        "total_replied": rate.get("total_replied", 0),
        "reply_rate_pct": rate.get("reply_rate_pct"),
    }


@router.get("/letters/stats")
def get_letter_stats():
    """누적 발송 카운터 — 전달됨 화면 + 홈 화면용"""
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    resp = httpx.get(
        f"{SUPABASE_URL}/rest/v1/letter_stats",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    rows = resp.json()
    stats = rows[0] if rows else {"total_sent": 0, "sent_last_7days": 0, "total_submitted": 0}
    return stats
