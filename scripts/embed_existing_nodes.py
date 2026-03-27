"""
기존 30개 ontology_nodes에 벡터 임베딩 생성
1회성 실행 스크립트

사용법:
  cd test017AI_Party_claudecode
  python scripts/embed_existing_nodes.py
"""

import os
import sys
import time
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# .env 먼저 로드 (OPENAI_API_KEY 필요)
from dotenv import load_dotenv
load_dotenv(Path(project_root) / "config" / ".env", override=True)

from db import supabase_admin
from services.ontology_matcher import create_embedding


def embed_all_nodes():
    """기존 ontology_nodes에 embedding 생성"""
    # embedding이 없는 노드만 대상
    nodes = supabase_admin.table("ontology_nodes") \
        .select("id, name, description") \
        .is_("embedding", "null") \
        .execute()

    total = len(nodes.data or [])
    print(f"임베딩 생성 대상: {total}개 노드")

    if total == 0:
        print("모든 노드에 이미 임베딩이 있습니다.")
        return

    success = 0
    failed = 0

    for i, node in enumerate(nodes.data):
        try:
            # 이름 + 설명을 합쳐서 임베딩
            text = f"{node['name']}. {node.get('description', '') or ''}"
            embedding = create_embedding(text)

            supabase_admin.table("ontology_nodes") \
                .update({"embedding": embedding}) \
                .eq("id", node["id"]) \
                .execute()

            success += 1
            print(f"  [{i+1}/{total}] {node['name']}")

            # Rate limit 방지 (text-embedding-3-small은 넉넉하지만 안전하게)
            if (i + 1) % 10 == 0:
                time.sleep(1)

        except Exception as e:
            failed += 1
            print(f"  [{i+1}/{total}] FAILED: {node['name']} - {e}")

    print(f"\n완료! 성공: {success}, 실패: {failed}")


if __name__ == "__main__":
    embed_all_nodes()
