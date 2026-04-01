"""
인증 의존성
- verify_app: 앱 클라이언트 인증 (쓰기 API 보호, 스팸 차단)
- verify_admin: 관리자 전용 엔드포인트 보호
외부 리뷰 반영 (2026-04-01)
"""

import os
from fastapi import Header, HTTPException


async def verify_app(x_app_key: str = Header(None)):
    """
    앱 클라이언트 인증 — 쓰기 API 스팸 방어
    - Railway 환경변수 APP_SECRET_KEY와 비교
    - Flutter 앱은 X-App-Key 헤더로 전송
    - 키 없거나 불일치 시 403
    """
    app_key = os.getenv("APP_SECRET_KEY")
    if not app_key:
        # APP_SECRET_KEY 미설정 시 인증 건너뜀 (개발 환경)
        return True
    if x_app_key != app_key:
        raise HTTPException(status_code=403, detail="앱 인증 실패")
    return True


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
