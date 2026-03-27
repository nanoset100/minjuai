# 민주AI 온톨로지 — 상세 실행 계획서

**작성자**: Claude Opus 4.6 (원 설계자)
**작성일**: 2026-03-27
**최종 수정**: 2026-03-27 (외부 검토 피드백 반영 v2.0)
**근거**: 3개 AI(Claude, ChatGPT, Grok) 종합 검토 + 실행 계획 외부 검토
**상태**: Phase 1 실행 중

---

## 외부 검토 반영 사항 (v2.0 변경점)

| # | 검토 피드백 | 반영 결과 |
|---|------------|-----------|
| Q1 | verified_count → upvotes/downvotes 분리 | ✅ verify_upvotes + verify_downvotes |
| Q1-2 | node_candidates에 first_report_id 추가 | ✅ 최초 제보 추적 가능 |
| Q3 | IVFFlat 인덱스 삭제 (30~150개에 불필요) | ✅ 주석 처리, 10,000개 이상 시 활성화 |
| Q4 | tenacity 재시도 → openai 내장 max_retries로 대체 | ✅ 의존성 최소화 |
| Q5 | 프롬프트 규칙 6번 추가 (억지 매칭 원천 차단) | ✅ 반영 |
| Q6 | pending 재시도 엔드포인트 추가 | ✅ /api/ontology/retry-pending |
| Q8 | API Key 인증 (Depends + X-Admin-Token) | ✅ dependencies.py |

---

## 현재 시스템 현황

### 기술 스택
| 구성 | 기술 | 호스팅 |
|------|------|--------|
| 백엔드 | Python FastAPI | Railway (자동 배포) |
| 데이터베이스 | PostgreSQL (Supabase) | Supabase Free Plan |
| 프론트엔드 | Flutter (Dart) | Google Play / App Store |
| AI | OpenAI GPT-4o mini | API 호출 |
| 리포지토리 | GitHub (nanoset100) | test017AI_Party_claudecode + minjuai-app |

### 현재 DB (Supabase)
- ontology_nodes: **30건** (issue 9, policy 3, global_case 18)
- ontology_edges: **29건** (solves, causes, similar_to, evidence_for, synergy_with)
- district_reports: **4건** (시민 제보)

### 현재 서버 구조 (main.py)
- POST /api/districts/report — 제보 등록 (DB 저장 + 포인트 적립만)
- GET /api/ontology/map — 전체 노드/엣지 반환
- GET /api/ontology/search — 노드 이름 검색

---

## Phase 1: DB 마이그레이션 ← 현재 단계

### 마이그레이션 파일
`migrations/012_ontology_pgvector.sql`

### 실행 방법
경수님이 Supabase SQL Editor에서 직접 실행

### 실행 내용 요약

```
STEP 1: CREATE EXTENSION vector         — pgvector 활성화
STEP 2: ALTER TABLE ontology_nodes      — embedding vector(1536) 컬럼 추가
STEP 3: CREATE TABLE report_node_links  — 제보↔노드 연결 테이블
STEP 4: ALTER TABLE district_reports    — ontology_status 컬럼 추가
STEP 5: CREATE TABLE node_candidates    — 미매칭 키워드 수집 테이블
STEP 6: (IVFFlat 인덱스 → 주석 처리)    — 외부 검토: 현재 규모에서 불필요
STEP 7: RLS 정책                        — service role 허용
STEP 8: RPC 함수 2개                    — match_ontology_nodes, find_similar_candidates
```

### 실행 후 검증 쿼리
```sql
SELECT
    (SELECT count(*) FROM information_schema.columns
     WHERE table_name = 'ontology_nodes' AND column_name = 'embedding') AS has_embedding,
    (SELECT count(*) FROM information_schema.tables
     WHERE table_name = 'report_node_links') AS has_rnl,
    (SELECT count(*) FROM information_schema.tables
     WHERE table_name = 'node_candidates') AS has_nc,
    (SELECT count(*) FROM information_schema.columns
     WHERE table_name = 'district_reports' AND column_name = 'ontology_status') AS has_status;
-- 결과: 모두 1이면 성공
```

---

## Phase 2: 서버 핵심 구현

### 새 파일 구조
```
test017AI_Party_claudecode/
├── main.py                          # 수정: BackgroundTasks + 새 엔드포인트 5개
├── dependencies.py                  # 신규: API Key 인증 (외부 검토 Q8)
├── services/
│   └── ontology_matcher.py          # 신규: 매칭 파이프라인 전체
├── scripts/
│   └── embed_existing_nodes.py      # 신규: 1회성 임베딩 생성
└── migrations/
    └── 012_ontology_pgvector.sql    # Phase 1 SQL
```

### 새 엔드포인트 목록
| 메서드 | 경로 | 용도 | 인증 |
|--------|------|------|------|
| POST | /api/districts/report | 수정: 백그라운드 매칭 추가 | 없음 |
| GET | /api/districts/report/{id}/ontology | 제보→연결 노드 조회 | 없음 |
| GET | /api/ontology/node/{id}/reports | 노드→관련 제보 조회 | 없음 |
| POST | /api/districts/report/{id}/verify-match | 시민 검증 | 없음 |
| GET | /api/ontology/stats | 모니터링 통계 | 없음 |
| POST | /api/ontology/retry-pending | pending 재매칭 | 관리자 |
| POST | /api/ontology/generate-batch | 노드 배치 생성 | 관리자 |
| POST | /api/ontology/approve-candidate/{id} | 후보 승인 | 관리자 |

### 핵심 매칭 파이프라인 흐름
```
시민 제보 제출
    │
    ▼
district_reports 저장 (즉시 응답, ontology_status='pending')
    │
    ▼ (BackgroundTasks — 비동기)
악성 제보 필터링
    │
    ├── 악성 → ontology_status='filtered', 종료
    │
    ▼
pgvector Top 10 후보 검색 (text-embedding-3-small)
    │
    ▼
GPT-4o mini 최종 매칭 (규칙 6개: 억지 매칭 원천 차단)
    │
    ├── 매칭 성공 → report_node_links 저장
    │                ontology_status='matched'
    │
    └── 매칭 실패 → node_candidates에 키워드 수집
                     ontology_status='unmatched'

※ Railway 배포 시 유실 대비: retry-pending 엔드포인트로 복구
```

### GPT 프롬프트 규칙 (최종본)
```
1. 정치적 좌우 편향 없이 중립적으로 판단하세요.
2. 관련성이 확실한 노드만 선택하세요. 억지로 연결하지 마세요.
3. 관련 노드가 없으면 빈 배열 []을 반환하세요.
4. relevance 점수가 0.3 미만인 연결은 제외하세요.
5. global_case(해외 사례) 타입은 시민 제보와 직접 연결하지 마세요.
6. 제공된 후보 노드 중 제보의 핵심 문제를 직접적으로 설명하거나
   해결하는 노드가 없다면, 절대 유추하여 연결하지 말고
   반드시 빈 배열을 반환하세요. (외부 검토 Q5 반영)
```

### OpenAI 클라이언트 설정 (외부 검토 Q4 반영)
```python
# tenacity 대신 openai 내장 재시도 사용 — 의존성 최소화
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    max_retries=3,
    timeout=30.0
)
```

### 관리자 인증 (외부 검토 Q8 반영)
```python
# dependencies.py
async def verify_admin(x_admin_token: str = Header(...)):
    if x_admin_token != os.getenv("ADMIN_SECRET_KEY"):
        raise HTTPException(status_code=403, detail="관리자 인증 실패")
    return True
```

---

## Phase 3: 노드 확장 (150~200개)

### 확장 대상 분야 (우선순위)
```
현재: 복지 (30개 노드)

1.  교통/도로         (issue 5 + policy 3)
2.  부동산/주거       (issue 5 + policy 3)
3.  교육             (issue 5 + policy 3)
4.  환경/기후         (issue 5 + policy 3)
5.  일자리/노동       (issue 5 + policy 3)
6.  안전/치안         (issue 5 + policy 3)
7.  의료/건강         (issue 3 + policy 2)
8.  청년 문제         (issue 3 + policy 2)
9.  AI/디지털         (issue 3 + policy 2)
10. 농어촌/지방소멸   (issue 3 + policy 2)

추가: ~120개 → 총 ~150개
```

---

## Phase 4: Flutter 앱 연동

### UI 변경 (제보 상세 화면)
```
┌─────────────────────────────────┐
│ 제보 상세                        │
│                                 │
│ 🧠 AI 분석 결과                  │
│ ├─ 🔴 노인복지 부족 (87%)        │
│ │   👍 3  👎 0                   │
│ │   [맞아요] [아니에요]           │
│ └─ 🟡 지역 간 격차 (62%)         │
│     👍 1  👎 0                   │
│     [맞아요] [아니에요]           │
└─────────────────────────────────┘
```

---

## 비용 추정 (외부 검토 Q7 검증 완료)

| 항목 | 월 7만 건 기준 | 비고 |
|------|---------------|------|
| text-embedding-3-small | ~$0.7 | 임베딩 생성 |
| GPT-4o mini | ~$10~13 | 매칭 판단 |
| **합계** | **~$15** | 외부 검토자 확인: "매우 현실적" |

---

## 전체 일정

| Phase | 작업 | 소요 | 상태 |
|-------|------|------|------|
| 1 | DB 마이그레이션 (SQL 실행) | 10분 | ← 현재 |
| 2-1 | ontology_matcher.py 작성 | 1세션 | 대기 |
| 2-2 | main.py 수정 + dependencies.py | 1세션 | 대기 |
| 2-3 | 기존 30개 노드 임베딩 생성 | 5분 | 대기 |
| 2-4 | Railway 배포 + 테스트 | 30분 | 대기 |
| 3 | 노드 확장 (150개) | 1~2세션 | 대기 |
| 4 | Flutter 앱 연동 | 2~3세션 | 대기 |

---

*3개 AI 검토 + 외부 실행 계획 검토 완료*
*경수님과 Claude Opus 4.6 협업 작성*
