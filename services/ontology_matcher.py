"""
온톨로지 매칭 서비스
3개 AI(Claude + ChatGPT + Grok) 종합 설계: pgvector 하이브리드 + GPT-4o mini
외부 검토 반영 v2.0 (2026-03-27)
"""

import os
import json
from openai import OpenAI
from db import supabase_admin

# OpenAI 클라이언트 (지연 초기화 — ai_client.py와 동일 패턴)
_client = None

def _get_openai_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        _client = OpenAI(
            api_key=api_key,
            max_retries=3,
            timeout=30.0
        )
    return _client


# ========== 1. 임베딩 생성 ==========

def create_embedding(text: str) -> list[float]:
    """텍스트를 1536차원 벡터로 변환 (text-embedding-3-small)"""
    response = _get_openai_client().embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


# ========== 2. pgvector 유사도 검색 (Top 10) ==========

def find_similar_nodes(text: str, match_count: int = 10, threshold: float = 0.3) -> list[dict]:
    """
    제보 텍스트와 유사한 온톨로지 노드 Top N 검색
    - pgvector 코사인 유사도 사용
    - Supabase RPC 함수 호출
    """
    print(f"[ONTOLOGY] 임베딩 생성 중...")
    embedding = create_embedding(text)
    print(f"[ONTOLOGY] 임베딩 생성 완료 (dim={len(embedding)})")

    print(f"[ONTOLOGY] Supabase RPC 호출 중...")
    # embedding을 문자열로 변환 (pgvector 호환성)
    embedding_str = str(embedding)
    result = supabase_admin.rpc("match_ontology_nodes", {
        "query_embedding": embedding_str,
        "match_threshold": threshold,
        "match_count": match_count
    }).execute()
    print(f"[ONTOLOGY] RPC 완료: {len(result.data or [])}개 결과")

    return result.data or []


# ========== 3. GPT-4o mini 최종 매칭 ==========

def match_report_to_nodes(report_title: str, report_content: str, candidate_nodes: list[dict]) -> list[dict]:
    """
    Top 10 후보 노드 중 실제 관련 있는 노드만 선별
    - GPT-4o mini 사용
    - relevance 0.3 미만 제외
    - 관련 없으면 빈 배열 반환
    - 좌우 중립적 판단
    """
    if not candidate_nodes:
        return []

    # 후보 노드 목록 구성
    nodes_text = "\n".join([
        f"- ID: {n['id']}, 타입: {n['type']}, 이름: {n['name']}, "
        f"설명: {n.get('description', '')[:100]}, 유사도: {n.get('similarity', 0):.2f}"
        for n in candidate_nodes
    ])

    prompt = f"""당신은 시민 제보와 정책 이슈를 연결하는 분석가입니다.

[규칙]
1. 정치적 좌우 편향 없이 중립적으로 판단하세요.
2. 관련성이 확실한 노드만 선택하세요. 억지로 연결하지 마세요.
3. 관련 노드가 없으면 빈 배열 []을 반환하세요.
4. relevance 점수가 0.3 미만인 연결은 제외하세요.
5. global_case(해외 사례) 타입은 시민 제보와 직접 연결하지 마세요.
6. 제공된 후보 노드 중 제보의 핵심 문제를 직접적으로 설명하거나 해결하는 노드가 없다면, 절대 유추하여 연결하지 말고 반드시 빈 배열을 반환하세요.

[시민 제보]
제목: {report_title}
내용: {report_content[:500]}

[후보 노드 목록]
{nodes_text}

[출력 형식] 반드시 JSON 객체로 반환. 다른 텍스트 없이.
{{"matches": [{{"node_id": "uuid", "relevance": 0.0~1.0, "reason": "매칭 이유 1줄"}}]}}
관련 노드가 없으면: {{"matches": []}}
"""

    response = _get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    try:
        content = response.choices[0].message.content
        parsed = json.loads(content)
        matches = parsed.get("matches", [])
        # relevance 0.3 미만 필터링
        return [m for m in matches if m.get("relevance", 0) >= 0.3]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return []


# ========== 4. 악성 제보 필터링 (기본) ==========

def is_malicious_report(title: str, content: str) -> bool:
    """
    기본 악성 제보 필터링
    - Phase 2: 간단한 규칙 기반
    - 나중에 AI 기반으로 고도화 가능
    """
    combined = (title + " " + content).lower()

    # 1. 너무 짧은 제보 (의미 없음)
    if len(content.strip()) < 10:
        return True

    # 2. 반복 문자 패턴 (스팸)
    if any(c * 10 in combined for c in "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅋㅎㅠㅜ"):
        return True

    # 3. 욕설/혐오 기본 필터 (확장 필요)
    blocked_patterns = ["시발", "씨발", "병신", "ㅅㅂ", "ㅂㅅ"]
    if any(p in combined for p in blocked_patterns):
        return True

    return False


# ========== 5. node_candidates 중복 방지 ==========

def add_or_merge_candidate(keyword: str, raw_snippet: str, report_id: str) -> dict:
    """
    미매칭 키워드를 node_candidates에 추가
    - pgvector로 기존 후보와 비교
    - similarity > 0.85이면 count만 증가
    - 새 키워드면 신규 추가
    - 외부 검토 반영: first_report_id 저장
    """
    embedding = create_embedding(keyword)

    # 기존 유사 후보 검색
    try:
        similar = supabase_admin.rpc("find_similar_candidates", {
            "query_embedding": embedding,
            "similarity_threshold": 0.85
        }).execute()
    except Exception:
        similar = type('obj', (object,), {'data': []})()

    if similar.data and len(similar.data) > 0:
        # 기존 후보와 유사 -> count 증가만
        existing = similar.data[0]
        new_count = existing["report_count"] + 1
        supabase_admin.table("node_candidates") \
            .update({
                "report_count": new_count,
                "updated_at": "now()"
            }) \
            .eq("id", existing["id"]) \
            .execute()
        return {"action": "merged", "candidate_id": existing["id"], "new_count": new_count}
    else:
        # 새 키워드 -> 신규 추가
        result = supabase_admin.table("node_candidates").insert({
            "keyword": keyword,
            "raw_text_snippet": raw_snippet[:300],
            "first_report_id": report_id,
            "report_count": 1,
            "embedding": embedding,
            "status": "pending"
        }).execute()
        return {"action": "created", "candidate_id": result.data[0]["id"] if result.data else None}


# ========== 6. 키워드 추출 ==========

def extract_keyword(title: str, content: str) -> str:
    """미매칭 제보에서 핵심 키워드 추출 (GPT-4o mini)"""
    try:
        response = _get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"""다음 시민 제보의 핵심 정책 키워드를 하나만 추출하세요.
예: "교통 체증", "학교 급식", "도로 보수", "주거 비용"

제목: {title}
내용: {content[:300]}

키워드만 반환 (따옴표 없이):"""}],
            temperature=0.1,
            max_tokens=20
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return title[:50]


# ========== 7. 전체 매칭 파이프라인 ==========

def process_report_ontology(report_id: str, title: str, content: str):
    """
    제보 등록 후 백그라운드에서 실행되는 전체 매칭 파이프라인

    흐름:
    1. 악성 제보 필터링
    2. pgvector Top 10 후보 검색
    3. GPT-4o mini 최종 매칭
    4. 매칭 성공 -> report_node_links 저장
    5. 매칭 실패 -> node_candidates에 키워드 수집
    """
    try:
        # Step 1: 악성 제보 필터링
        if is_malicious_report(title, content):
            supabase_admin.table("district_reports") \
                .update({"ontology_status": "filtered"}) \
                .eq("id", report_id) \
                .execute()
            print(f"[ONTOLOGY] 필터링됨: {report_id}")
            return

        # Step 2: pgvector Top 10 후보 검색
        print(f"[ONTOLOGY] Step 2 시작: 임베딩 생성 중... {report_id}")
        combined_text = f"{title} {content}"
        try:
            candidates = find_similar_nodes(combined_text, match_count=10, threshold=0.3)
            print(f"[ONTOLOGY] Step 2 완료: 후보 {len(candidates)}개 발견")
        except Exception as e2:
            print(f"[ONTOLOGY] Step 2 실패 (pgvector 검색): {type(e2).__name__}: {e2}")
            raise

        # Step 3: GPT-4o mini 최종 매칭
        if candidates:
            matches = match_report_to_nodes(title, content, candidates)
        else:
            matches = []

        # Step 4a: 매칭 성공
        if matches:
            for match in matches:
                try:
                    supabase_admin.table("report_node_links").insert({
                        "report_id": report_id,
                        "node_id": match["node_id"],
                        "relevance": match.get("relevance", 0.5),
                        "match_reason": match.get("reason", ""),
                        "ai_match_version": "gpt-4o-mini",
                        "verify_upvotes": 0,
                        "verify_downvotes": 0
                    }).execute()
                except Exception as e:
                    print(f"[ONTOLOGY] 링크 저장 실패 (중복?): {e}")

            supabase_admin.table("district_reports") \
                .update({"ontology_status": "matched"}) \
                .eq("id", report_id) \
                .execute()
            print(f"[ONTOLOGY] 매칭 성공: {report_id} -> {len(matches)}개 노드")

        # Step 4b: 매칭 실패 -> 키워드 수집
        else:
            keyword = extract_keyword(title, content)
            if keyword:
                add_or_merge_candidate(keyword, content[:300], report_id)
                print(f"[ONTOLOGY] 미매칭 키워드 수집: '{keyword}' from {report_id}")

            supabase_admin.table("district_reports") \
                .update({"ontology_status": "unmatched"}) \
                .eq("id", report_id) \
                .execute()

    except Exception as e:
        print(f"[ONTOLOGY] 매칭 오류: {report_id} - {e}")
        try:
            supabase_admin.table("district_reports") \
                .update({"ontology_status": "error"}) \
                .eq("id", report_id) \
                .execute()
        except Exception:
            pass
