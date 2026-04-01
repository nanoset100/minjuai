# 외부 AI 리뷰 요청: 민주AI 백엔드 현황 진단

**작성일**: 2026-04-01
**작성자**: Claude Opus 4.6 (프로젝트 담당 AI)
**목적**: 솔직한 현황 공유 + 구체적 질문에 대한 피드백 요청

---

## 프로젝트 개요

**민주AI** — 세계 최초 AI 운영 정당 앱 (1인 개발)
- **프론트엔드**: Flutter (모바일 앱)
- **백엔드**: Python FastAPI + Supabase (PostgreSQL + pgvector)
- **배포**: Railway (https://minjuai-production.up.railway.app)
- **AI**: OpenAI GPT-4o mini (텍스트→정책 이슈 매칭), text-embedding-3-small (벡터)
- **목표**: 시민 제보 → AI가 정책 이슈와 연결 → 같은 문제를 겪는 시민끼리 연대

---

## 현재 아키텍처

### 핵심 흐름
```
시민이 제보 작성
  → AI가 258개 정책 이슈(온톨로지) 중 후보 3~5개 추천
  → 시민이 직접 이슈 선택 (또는 "해당 없음")
  → 같은 이슈 N명 참여 중 표시 (연대감)
  → 이슈별 지역 히트맵 (방금 구현)
```

### AI 매칭 파이프라인
```
제보 텍스트
  → OpenAI text-embedding-3-small (1536차원 벡터)
  → pgvector 코사인 유사도 Top 10 검색 (threshold 0.3)
  → GPT-4o mini가 최종 필터링 (relevance 0.3~1.0)
  → report_node_links 테이블에 저장
```
- 현재 AI 자동 매칭 정확도: 37% (3번 중 2번 틀림)
- 그래서 "시민이 직접 선택"하는 전략으로 전환함 (Strategy Phase 1)

### DB 스키마 (핵심 테이블)
```
ontology_nodes (258개)
  - id, type, name, description, category, embedding(vector 1536)
  - 7개 카테고리: 복지, 교육, 경제, 정치, 환경, 안전, 생활

district_reports (시민 제보, 현재 ~10건)
  - id, district("서울 영등포구을"), title, content
  - ontology_status: pending → matched/unmatched/citizen_none

report_node_links (제보↔이슈 연결)
  - report_id, node_id, relevance(0~1)
  - citizen_selected(bool), matched_by("ai"/"citizen")
  - verify_upvotes, verify_downvotes

node_candidates (미매칭 키워드 → 온톨로지 성장용)
```

### 코드 구조
```
main.py           — 1946줄, 64개 엔드포인트 (전부 이 파일에)
db.py             — Supabase 클라이언트 2개 (anon + service_key)
dependencies.py   — verify_admin 미들웨어
services/
  ontology_matcher.py — AI 매칭 파이프라인
agents/
  support_agent.py    — 챗봇
  analytics_agent.py  — 분석
  monitoring_agent.py — 국회의원 감시
  policy_agent.py     — 정책 분석
  marketing_agent.py  — SNS 콘텐츠
  policy_research_agent.py — 주간 리서치
  batch_helper.py     — 배치 작업
migrations/       — SQL 마이그레이션 12개
```

---

## 솔직한 자기 진단 (문제점)

### 1. main.py가 1946줄짜리 모놀리스
- 64개 엔드포인트가 한 파일에 전부 있음
- FastAPI Router 분리를 안 함
- 이유: 1인 개발이라 빠르게 기능 추가하다 보니 이렇게 됨

### 2. 인증/보안이 거의 없음
- `verify_admin` 사용: **1곳만** (retry-pending)
- 나머지 63개 API는 **누구나 호출 가능**
  - 투표 API, 제보 등록, 이슈 선택 등 전부 열려 있음
  - 악의적으로 투표 조작, 제보 스팸 가능
- CORS: `allow_origins=["*"]` (완전 개방)
- Rate limiting: 없음

### 3. 히트맵 API 스케일링
```python
# report_node_links 테이블 전체를 한 번에 가져옴 (limit 없음!)
query = supabase_admin.table("report_node_links") \
    .select("node_id, citizen_selected, relevance, "
            "district_reports(id, district), "
            "ontology_nodes(id, name, category)")
result = query.execute()  # 데이터 커지면 위험
```
- 현재 22건이라 괜찮지만, 목표 월 7만 건이면 터짐
- Supabase 클라이언트가 GROUP BY 미지원 → Python에서 집계 중
- 해결책: Supabase RPC (PostgreSQL 함수)로 전환해야 함

### 4. N+1 쿼리 문제
```python
# get_report_ontology에서 노드별로 개별 카운트 쿼리
for nid in set(node_ids):
    cnt = supabase_admin.table("report_node_links") \
        .select("id", count="exact") \
        .eq("node_id", nid) \
        .eq("citizen_selected", True) \
        .execute()
    participant_counts[nid] = cnt.count or 0
```
- 노드 5개면 5번 쿼리, 10개면 10번 쿼리

### 5. AI 매칭 정확도 37%
- pgvector 유사도 검색 → GPT-4o mini 필터링인데 정확도 낮음
- 원인 추정: 258개 노드 중 228개가 시민 이슈(긴 문장형 이름)로, 임베딩 품질이 불균일
- 시민 직접 선택으로 우회했지만, 근본 해결은 아님

### 6. 에러 핸들링
- 전 엔드포인트가 `try/except Exception → 500` 패턴
- 400 (잘못된 요청), 404 (없는 리소스) 구분 없이 전부 500 반환

### 7. 테스트 코드 0개
- 단위 테스트, 통합 테스트 전무
- 수동으로 curl 테스트만 하고 있음

---

## 잘 한 부분 (균형 잡기)

1. **데이터 모델 설계**: ontology_nodes + report_node_links + citizen_selected 구조는 확장성 있음
2. **전략 전환 판단**: AI 정확도 37%를 인정하고, "시민이 선택" 전략으로 빠르게 피벗
3. **pgvector 활용**: 벡터 유사도 검색 인프라는 제대로 갖춤
4. **비용 효율**: GPT-4o mini + text-embedding-3-small로 월 ~$15 운영 가능
5. **시민 참여 루프**: 제보→선택→연대→히트맵 흐름이 논리적으로 연결됨

---

## 구체적 질문 (피드백 요청)

### Q1. main.py 분리 전략
1946줄 모놀리스를 분리하고 싶은데, 1인 개발자가 가장 효율적으로 할 수 있는 방법은? FastAPI Router로 어떤 단위로 나누는 게 좋을까? (현재 64개 엔드포인트)

### Q2. 인증 전략
1인 개발, Flutter 앱이 클라이언트인 상황에서 가장 가벼운 인증 방법은? Supabase Auth를 쓰는 게 맞나, 아니면 다른 방법이 있나? 특히 투표/제보 등 사용자 행동에 대한 최소한의 보호.

### Q3. 히트맵 스케일링
월 7만 건 제보 시나리오에서 히트맵 집계를 어떻게 해야 할까?
- Supabase RPC (PostgreSQL 함수)로 GROUP BY?
- Materialized View?
- 캐시 전략?
- 현재 규모(22건)에서 미리 최적화하는 게 맞나, 아니면 나중에 해도 되나?

### Q4. AI 매칭 정확도 개선
37% 정확도의 근본 원인과 개선 방법은?
- 258개 노드 중 228개가 "시민이 작성한 긴 문장형 이슈"인데 임베딩이 제대로 될까?
- 시민 선택 데이터(citizen_selected)가 100건, 500건 쌓이면 어떤 방식으로 활용하는 게 좋을까?
- fine-tuning vs few-shot vs 단순 키워드 매칭 중 현실적 선택은?

### Q5. 전체 아키텍처 판단
"1인 개발자 + FastAPI + Supabase + Railway + Flutter" 스택으로 "월 7만 건 제보, 수천 명 동시 사용자" 목표를 달성할 수 있나? 어디서 병목이 올까?

### Q6. 우선순위 조언
다음 중 지금 가장 먼저 해야 할 것은?
1. main.py 라우터 분리
2. 인증 추가
3. 테스트 코드 작성
4. 히트맵 성능 최적화
5. Strategy Phase 4 (새 이슈 제안 기능) 개발 계속
6. AI 매칭 정확도 개선

---

## 현재 수치 요약

| 항목 | 수치 |
|------|------|
| 엔드포인트 | 64개 |
| main.py 줄 수 | 1,946줄 |
| 온톨로지 노드 | 258개 (7개 카테고리) |
| 시민 제보 | ~10건 |
| AI 매칭 정확도 | 37% |
| 인증된 엔드포인트 | 1/64개 |
| 테스트 코드 | 0개 |
| 월 운영비 | ~$15 |
| 배포 환경 | Railway (단일 인스턴스) |

---

*이 문서는 프로젝트 담당 AI(Claude Opus 4.6)가 솔직하게 작성했습니다.*
*과장이나 축소 없이 현재 상태를 있는 그대로 전달합니다.*
*피드백을 주시면 즉시 반영하겠습니다.*
