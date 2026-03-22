#!/usr/bin/env python3
"""Supabase SQL 직접 실행 (postgrest SQL function 활용)"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

import httpx

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def execute_sql(sql: str):
    """Supabase SQL API 직접 호출"""
    # Supabase pg REST 쿼리 - sql 쿼리 실행을 위한 rpc
    # 먼저 exec_sql 함수 생성 시도
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    # Supabase SQL API (Management API가 아닌 Database Function 방식)
    # 직접 postgREST를 우회해서 실행
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"

    resp = httpx.post(url, headers=headers, json={"sql_text": sql}, timeout=60)
    return resp.status_code, resp.text


def main():
    migration_dir = Path(__file__).parent

    # 먼저 exec_sql 함수 생성
    print("1. exec_sql 함수 생성 시도...")

    create_func_sql = """
    CREATE OR REPLACE FUNCTION exec_sql(sql_text TEXT)
    RETURNS TEXT
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        EXECUTE sql_text;
        RETURN 'OK';
    END;
    $$;
    """

    # 이 함수를 만들기 위해서도 SQL 실행이 필요하므로
    # supabase-py를 통해 직접 실행 시도
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        # rpc 호출 시도
        try:
            result = client.rpc('exec_sql', {'sql_text': 'SELECT 1'}).execute()
            print("   exec_sql 함수가 이미 존재합니다!")
        except Exception:
            print("   exec_sql 함수가 없습니다. Supabase Dashboard에서 생성 필요.")
            print("\n" + "="*60)
            print("  아래 내용을 Supabase SQL Editor에 붙여넣고 실행하세요:")
            print("  https://supabase.com/dashboard/project/iymvskaxjmgpyatyeqec/sql")
            print("="*60)

            # 통합 SQL 파일 읽기
            combined = migration_dir / "combined_migration.sql"
            if combined.exists():
                sql = combined.read_text(encoding='utf-8')
                print(f"\n  파일: {combined}")
                print(f"  크기: {len(sql)} bytes")

                # SQL 파일을 더 쉽게 복사할 수 있도록 클립보드에 복사 시도
                try:
                    import subprocess
                    process = subprocess.Popen(['clip'], stdin=subprocess.PIPE)
                    process.communicate(sql.encode('utf-8'))
                    print("\n  ✅ SQL이 클립보드에 복사되었습니다!")
                    print("  Supabase SQL Editor에서 Ctrl+V로 붙여넣고 Run 클릭!")
                except Exception:
                    print("\n  클립보드 복사 실패. 파일을 직접 열어 복사하세요.")

            return

        # exec_sql이 있으면 마이그레이션 실행
        print("\n2. 마이그레이션 실행...")

        sql_files = sorted(migration_dir.glob("[0-9]*.sql"))
        for sql_file in sql_files:
            sql = sql_file.read_text(encoding='utf-8')
            print(f"\n   실행 중: {sql_file.name}")

            try:
                result = client.rpc('exec_sql', {'sql_text': sql}).execute()
                print(f"   ✅ 성공!")
            except Exception as e:
                # 개별 statement로 분리해서 실행
                print(f"   전체 실행 실패, 개별 실행 시도...")
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

                ok = 0
                fail = 0
                for stmt in statements:
                    try:
                        client.rpc('exec_sql', {'sql_text': stmt}).execute()
                        ok += 1
                    except Exception as e2:
                        fail += 1
                        err_msg = str(e2)[:80]
                        print(f"      ⚠ {err_msg}")

                print(f"   결과: {ok} 성공, {fail} 실패")

        print("\n✅ 마이그레이션 완료!")

    except ImportError:
        print("supabase 패키지가 설치되지 않았습니다: pip install supabase")


if __name__ == "__main__":
    main()
