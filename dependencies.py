"""
인증 의존성
- verify_user: 사용자 인증 (Supabase JWT 검증)
- verify_app: 앱 클라이언트 인증 (쓰기 API 보호, 스팸 차단)
- verify_admin: 관리자 전용 엔드포인트 보호
"""

import os
import jwt
from fastapi import Header, HTTPException


async def verify_user(authorization: str = Header(None)):
    """
    Supabase Auth JWT 검증 — 사용자 인증
    - Flutter 앱이 Authorization: Bearer <token> 헤더로 전송
    - JWT_SECRET 미설정 시 인증 건너뜀 (개발 환경)
    - 검증 성공 시 user_id 반환
    """
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    if not jwt_secret:
        # JWT_SECRET 미설정 시 인증 건너뜀 (개발 환경)
        return {"sub": "dev-user", "email": "dev@local"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다. 다시 로그인해주세요")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")


async def verify_app(x_app_key: str = Header(None)):
    """
    앱 클라이언트 인증 — 쓰기 API 스팸 방어
    - Railway 환경변수 APP_SECRET_KEY와 비교
    - Flutter 앱은 X-App-Key 헤더로 전송
    - 키 없거나 불일치 시 403
    """
    app_key = os.getenv("APP_SECRET_KEY")
    if not app_key:
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
