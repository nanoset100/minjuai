"""
Word 파일에서 228건의 실제 시민 이슈를 파싱하여
ontology_nodes에 INSERT + 임베딩 생성

사용법: python scripts/import_ontology_from_docx.py
"""

import os
import sys
import json
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docx import Document
from db import supabase_admin
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "").strip(),
    max_retries=3,
    timeout=30.0
)

DOCX_PATH = r"M:\디지털작업방\미래코드당\인쇄용PDF\민주AI 온톨로지' 구축을 위한 52개 전 분야.docx"

# 대분류 매핑 (주제 번호 → 대분류)
CATEGORY_MAP = {
    range(1, 7): "경제",      # 1~6
    range(7, 19): "사회",     # 7~18
    range(19, 29): "생활",    # 19~28 (28=통일대비, 0건)
    range(29, 37): "정치",    # 29~36
    range(37, 45): "환경",    # 37~44
    range(45, 53): "미래",    # 45~52
}

def get_category(topic_num):
    for r, cat in CATEGORY_MAP.items():
        if topic_num in r:
            return cat
    return "기타"


def get_source_tag(text):
    for tag in ['청원', '뉴스', '시민단체', '연구', '주민참여예산']:
        if f'[{tag}]' in text:
            return tag
    return ''


def create_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def parse_docx():
    doc = Document(DOCX_PATH)
    nodes = []
    current_topic_name = ""
    current_topic_num = 0

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue

        # 주제 헤더 (예: "1. 경제·일자리 (총 5건 확인됨)")
        if text and text[0].isdigit() and '(' in text and '건' in text:
            # 번호 추출
            num_str = text.split('.')[0].strip()
            try:
                current_topic_num = int(num_str)
            except ValueError:
                continue
            # 주제명 추출 (번호 뒤 ~ 괄호 전)
            name_part = text.split('(')[0].strip()
            # "1. 경제·일자리" → "경제·일자리"
            current_topic_name = '.'.join(name_part.split('.')[1:]).strip()
            continue

        # issue 또는 policy 항목
        if text.startswith('issue') or text.startswith('policy'):
            node_type = 'issue' if text.startswith('issue') else 'policy'
            source = get_source_tag(text)
            category = get_category(current_topic_num)

            # "issue : 내용 [출처]" → "내용"
            content = text.split(':', 1)[1].strip() if ':' in text else text
            # 출처 태그 제거
            for tag in ['[청원]', '[뉴스]', '[시민단체]', '[연구]', '[주민참여예산]']:
                content = content.replace(tag, '').strip()
            # 끝의 쉼표 제거
            content = content.rstrip(',').strip()

            # 이름은 앞 50자, 설명은 전체
            name = content[:80] if len(content) > 80 else content
            description = content

            nodes.append({
                'type': node_type,
                'name': name,
                'description': description,
                'category': category,
                'topic': current_topic_name,
                'source': source,
                'topic_num': current_topic_num
            })

    return nodes


def main():
    print("=" * 60)
    print("민주AI 온톨로지 Phase 3: 실제 시민 이슈 데이터 임포트")
    print("=" * 60)

    # 1. Word 파일 파싱
    print("\n[1/3] Word 파일 파싱 중...")
    nodes = parse_docx()
    print(f"  파싱 완료: {len(nodes)}건")
    print(f"  issue: {sum(1 for n in nodes if n['type'] == 'issue')}건")
    print(f"  policy: {sum(1 for n in nodes if n['type'] == 'policy')}건")

    # 카테고리별 통계
    cats = {}
    for n in nodes:
        cats[n['category']] = cats.get(n['category'], 0) + 1
    print(f"  카테고리별: {cats}")

    # 2. DB INSERT
    print("\n[2/3] ontology_nodes에 INSERT 중...")
    inserted = 0
    failed = 0
    for i, node in enumerate(nodes):
        try:
            data = {
                'type': node['type'],
                'name': node['name'],
                'description': node['description'],
                'category': node['category'],
                'data': json.dumps({
                    'source': node['source'],
                    'topic': node['topic'],
                    'topic_num': node['topic_num']
                }, ensure_ascii=False)
            }
            supabase_admin.table("ontology_nodes").insert(data).execute()
            inserted += 1
            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{len(nodes)}] 진행 중...")
        except Exception as e:
            failed += 1
            print(f"  [ERROR] {node['name'][:40]}: {e}")

    print(f"  INSERT 완료: 성공 {inserted}, 실패 {failed}")

    # 3. 임베딩 생성
    print("\n[3/3] 임베딩 생성 중 (새로 추가된 노드만)...")
    new_nodes = supabase_admin.table("ontology_nodes") \
        .select("id, name, description") \
        .is_("embedding", "null") \
        .execute()

    total = len(new_nodes.data)
    print(f"  임베딩 대상: {total}개 노드")

    for i, node in enumerate(new_nodes.data):
        try:
            text = f"{node['name']}. {node.get('description', '')}"
            embedding = create_embedding(text)
            supabase_admin.table("ontology_nodes") \
                .update({"embedding": embedding}) \
                .eq("id", node["id"]) \
                .execute()
            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{total}] 진행 중...")
        except Exception as e:
            print(f"  [ERROR] {node['name'][:40]}: {e}")
        # Rate limit 방지
        if (i + 1) % 50 == 0:
            time.sleep(1)

    print(f"  임베딩 완료!")

    # 4. 최종 확인
    total_nodes = supabase_admin.table("ontology_nodes") \
        .select("id", count="exact").execute()
    total_with_embedding = supabase_admin.table("ontology_nodes") \
        .select("id") \
        .not_.is_("embedding", "null") \
        .execute()

    print("\n" + "=" * 60)
    print("결과 요약")
    print("=" * 60)
    print(f"총 노드 수: {total_nodes.count}")
    print(f"임베딩 완료: {len(total_with_embedding.data)}")
    print("Phase 3 완료!")


if __name__ == "__main__":
    main()
