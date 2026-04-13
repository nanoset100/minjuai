"""
routers/ai_polish.py
AI 다듬기 API — 사용자 버튼 클릭 시에만 호출 (자동 변환 금지)

POST /api/ai/polish  — 편지/문의 텍스트 다듬기 (GPT-4o mini)
"""

import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI

router = APIRouter(prefix="/api", tags=["ai"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

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
def polish_content(req: PolishRequest):
    """AI 다듬기 — 사용자가 버튼을 클릭했을 때만 호출"""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="AI 서비스를 사용할 수 없습니다")

    type_label = "문의" if req.type == "inquiry" else "편지"

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 다듬기 중 오류가 발생했습니다: {str(e)}")
