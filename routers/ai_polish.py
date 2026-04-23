"""
routers/ai_polish.py
AI 다듬기 API — 사용자 버튼 클릭 시에만 호출 (자동 변환 금지)

POST /api/ai/polish  — 편지/문의 텍스트 다듬기 (GPT-4o mini)

Rate limit: IP당 분당 5회 / 일 20회
"""

import os
import time
from collections import defaultdict, deque
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from openai import OpenAI

router = APIRouter(prefix="/api", tags=["ai"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ─── Rate Limiter (외부 라이브러리 없이 in-memory) ─────────────
# {ip: deque([timestamp, ...])}
_rate_per_minute: dict[str, deque] = defaultdict(deque)
_rate_per_day: dict[str, deque] = defaultdict(deque)

LIMIT_PER_MINUTE = 5
LIMIT_PER_DAY = 20


def check_rate_limit(ip: str) -> None:
    """IP 기반 rate limit 검사. 초과 시 HTTPException(429) 발생"""
    now = time.time()

    # 분당 제한
    minute_q = _rate_per_minute[ip]
    while minute_q and now - minute_q[0] > 60:
        minute_q.popleft()
    if len(minute_q) >= LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"잠깐! 1분에 {LIMIT_PER_MINUTE}회까지만 다듬기를 요청할 수 있어요. 잠시 후 다시 시도해주세요."
        )

    # 일 제한
    day_q = _rate_per_day[ip]
    while day_q and now - day_q[0] > 86400:
        day_q.popleft()
    if len(day_q) >= LIMIT_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"오늘 AI 다듬기 횟수({LIMIT_PER_DAY}회)를 모두 사용했어요. 내일 다시 시도해주세요."
        )

    # 카운트 기록
    minute_q.append(now)
    day_q.append(now)


def get_client_ip(request: Request) -> str:
    """실제 클라이언트 IP 추출 (프록시/Railway 환경 대응)"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ─── 프롬프트 ────────────────────────────────────────────────────
POLISH_PROMPT = """다음 시민 {type_label}을 의원실 전달에 적합하게 다듬어 주세요.

원문:
{content}

규칙:
- 의미와 요청 사항은 절대 변경하지 않는다
- 비속어/감정적 표현을 정중한 표현으로 교체
- 문장 구조를 자연스럽게 정리
- 200자~1000자 범위 유지
- 한국어로만 작성

다듬어진 내용만 반환 (설명 없이):"""


class PolishRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=2000, description="다듬을 원문")
    type: str = Field(default="letter", pattern="^(letter|inquiry)$")


@router.post("/ai/polish")
def polish_content(req: PolishRequest, request: Request):
    """AI 다듬기 — 사용자가 버튼을 클릭했을 때만 호출"""
    # 1. Rate limit 검사
    ip = get_client_ip(request)
    check_rate_limit(ip)

    # 2. API 키 확인
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="AI 서비스를 사용할 수 없습니다")

    type_label = "문의" if req.type == "inquiry" else "편지"

    # 3. GPT 호출
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": POLISH_PROMPT.format(
                    type_label=type_label,
                    content=req.content,
                )
            }],
            temperature=0.3,
            max_tokens=800,
        )
        polished = response.choices[0].message.content.strip()

        return {
            "polished": polished,
            "original": req.content,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 다듬기 중 오류가 발생했습니다: {str(e)}")
