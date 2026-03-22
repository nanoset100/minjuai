#!/usr/bin/env python3
"""
Supabase 마이그레이션 실행 스크립트
SQL 파일을 읽어서 Supabase에 실행
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

import httpx

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def run_sql(sql: str, description: str = ""):
    """Supabase REST API로 SQL 실행"""
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"

    # Supabase는 직접 SQL 실행이 안되므로 postgrest를 우회
    # 대신 supabase-py의 직접 쿼리 사용
    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # SQL을 개별 statement로 분리
    statements = []
    current = []
    for line in sql.split('\n'):
        stripped = line.strip()
        if stripped.startswith('--') or not stripped:
            continue
        current.append(line)
        if stripped.endswith(';'):
            statements.append('\n'.join(current))
            current = []

    if current:
        statements.append('\n'.join(current))

    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"  {len(statements)}개 SQL 구문 실행")
    print(f"{'='*60}")

    success = 0
    errors = 0

    for i, stmt in enumerate(statements, 1):
        try:
            # postgrest rpc 호출 대신 직접 HTTP 요청
            resp = httpx.post(
                f"{SUPABASE_URL}/rest/v1/rpc/",
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json",
                },
                json={"query": stmt},
                timeout=30,
            )
            if resp.status_code < 400:
                success += 1
                print(f"  [{i}/{len(statements)}] OK")
            else:
                # postgrest rpc가 없으면 SQL Editor로 직접 실행 필요
                errors += 1
                print(f"  [{i}/{len(statements)}] HTTP {resp.status_code}")
        except Exception as e:
            errors += 1
            print(f"  [{i}/{len(statements)}] Error: {e}")

    return success, errors


def main():
    migration_dir = Path(__file__).parent
    sql_files = sorted(migration_dir.glob("*.sql"))

    if not sql_files:
        print("SQL 파일이 없습니다.")
        return

    print("\n민주AI 데이터베이스 마이그레이션")
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"SQL 파일: {len(sql_files)}개")

    # SQL 파일들을 하나로 합쳐서 출력
    print("\n" + "="*60)
    print("  Supabase SQL Editor에서 직접 실행해주세요")
    print("  https://supabase.com/dashboard → SQL Editor")
    print("="*60)

    combined_sql = ""
    for sql_file in sql_files:
        sql = sql_file.read_text(encoding='utf-8')
        combined_sql += f"\n-- ========== {sql_file.name} ==========\n"
        combined_sql += sql + "\n"

    # 통합 SQL 파일 저장
    combined_path = migration_dir / "combined_migration.sql"
    combined_path.write_text(combined_sql, encoding='utf-8')
    print(f"\n  통합 SQL 파일 저장: {combined_path}")
    print(f"  이 파일의 내용을 Supabase SQL Editor에 붙여넣고 실행하세요.")

    print("\n" + combined_sql[:500] + "...\n")


if __name__ == "__main__":
    main()
