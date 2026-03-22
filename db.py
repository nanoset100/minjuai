"""
Supabase 데이터베이스 클라이언트
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 로드
env_path = Path(__file__).parent / "config" / ".env"
load_dotenv(env_path, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# 공개 클라이언트 (RLS 적용, 프론트엔드용)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# 관리자 클라이언트 (RLS 우회, 백엔드 전용)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
