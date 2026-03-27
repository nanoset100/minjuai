"""
관리자 인증 의존성
외부 검토 Q8 반영: API Key 방식 (Depends + X-Admin-Token)
"""

import os
from fastapi import Header, HTTPException


async def verify_admin(x_admin_token: str = Header(...)):
    """
    관리자 전용 엔드포인트 보호
    - Railway 환경변수 ADMIN_SECRET_KEY와 비교
    - 클라이언트는 X-Admin-Token 헤더로 전송
    """
    admin_key = os.getenv("ADMIN_SECRET_KEY")
    if not admin_key or x_admin_token != admin_key:
        raise HTTPException(status_code=403, detail="관리자 인증 실패")
    return True
