# 민주AI 온톨로지 시스템 — 종합 검토 보고서 (v2 완성판)

**작성자**: Claude Opus 4.6 (원 설계자)
**작성일**: 2026-03-27
**목적**: 3개 AI(Claude, ChatGPT, Grok) 검토 결과를 종합하여 최종 실행 계획 수립
**버전**: v2 — Grok 리포트 전문 반영 완료

---

## 1. 검토 참여 AI 및 역할

| AI | 역할 | 리포트 |
|----|------|--------|
| Claude Opus 4.6 | 원 설계자 — 자체 평가 및 솔직한 결함 고백 | 내부 리포트 |
| ChatGPT (GPT-4o) | 외부 검토자 — pgvector 기반 대안 제시 | ontology_pgvector.md |
| Grok (xAI) | 외부 검토자 — 총점 8.7/10, 실전 운영 관점 피드백 | ONTOLOGY_REVIEW_GROK.md |

---

## 2. 전체 타임라인 요약

```
[1차 설계] JSONB 태그 방식 ("가짜 온톨로지")
    → 발견: ontology_tags JSONB 컬럼 = 그냥 AI 메타데이터
    → 판정: ❌ 완전 실패 — 온톨로지가 아님
    → 조치: 서버/DB/앱 전체 원상복구 완료

[2차 설계] report_node_links 분리 테이블
    → 발견: ontology_edges에 제보→노드 엣지 불가능 (FK 제약)
    → 판정: △ 구조 개선했으나 운영 고려 부족
    → 조치: 3차 설계로 발전

[3차 설계] 비동기 매칭 + 시민 검증 + 노드 후보 수집
    → ChatGPT 검토: pgvector 하이브리드 방식 제안
    → Grok 검토: 8.7/10, 노드 편향 치명적 + 실전 운영 제안 다수
    → 현재: 3개 AI 종합 후 최종 설계 확정
```

---

## 3. 6개 핵심 질문 — 3개 AI 의견 종합

### Q1. 아키텍처 적절성 (report_node_links 분리)

| AI | 판정 | 핵심 의견 |
|----|------|-----------|
| Claude | ✅ 적절 | ontology 그래프 오염 방지, 양방향 조회 가능 |
| ChatGPT | ✅ "교과서적인 RDBMS 기반 그래프 모델링" | 개념(Class)과 사건(Instance) 분리가 정확 |
| Grok | ✅ "최고의 선택, 그대로 진행" | many-to-many 연결 + 메타데이터 관리 자연스러움 |

**🟢 만장일치: report_node_links 분리 테이블 확정**

---

### Q2. 노드 편향 해결 (현재 30개 = 전부 복지)

| AI | 판정 | 핵심 의견 |
|----|------|-----------|
| Claude | ⚠️ 치명적 약점 | 교통/환경/교육 제보 시 매칭 불가 |
| ChatGPT | ⚠️ "명백한 약점" | Top 10 분야 × 5~10개 시드 = ~100개로 70% 커버 |
| Grok | ⚠️ "가장 큰 약점 (치명적)" | **150~200개 목표**, 배치 생성 엔드포인트 제안 |

**🔴 만장일치: 가장 시급한 문제**

**ChatGPT vs Grok 비교:**

| 항목 | ChatGPT | Grok |
|------|---------|------|
| 목표 노드 수 | ~100개 | **150~200개** |
| 생성 방법 | 수동/AI 시드 | **FastAPI 배치 엔드포인트** `/api/ontology/generate_batch` |
| 데이터 소스 | 국회 입법처/통계청 | **기존 DB의 policy_topics, global_cases, weekly_research 활용** |
| 분야 예시 | 교통, 부동산, 교육, 환경, 일자리 등 | + AI/디지털, 청년, 농어촌, 지방소멸 |

**Claude 종합 결론:**
> Grok의 "기존 DB 데이터를 활용한 배치 생성" 제안이 더 현실적입니다.
> 이미 policy_topics, global_cases 테이블에 다양한 분야 데이터가 있으므로,
> 이를 기반으로 노드를 생성하면 외부 자료를 찾을 필요 없이 빠르게 확장 가능.
> 목표: **150개 이상**, 배치 엔드포인트 방식 채택.

---

### Q3. AI 매칭 방식

| AI | 판정 | 핵심 의견 |
|----|------|-----------|
| Claude | GPT-4o mini에 노드 목록 전체 전달 | 30개는 가능, 100개 넘으면 문제 |
| ChatGPT | ❌ "프롬프트 주입 방식 폐기" | pgvector + Top **5** 후보 → GPT-4o mini |
| Grok | ❌ 동일 판단 | pgvector + Top **10** 후보 → GPT-4o mini |

**🟢 만장일치: pgvector 하이브리드 매칭 채택**

```
[Claude 원래 설계] — 노드가 많아지면 파탄
제보 텍스트 → GPT-4o mini에 전체 노드 전달 → 매칭

[ChatGPT + Grok 공통 제안: 하이브리드 RAG 패턴]
제보 텍스트 → text-embedding-3-small로 벡터화 (저렴)
           → pgvector 코사인 유사도로 Top N 후보 검색 (무료, <0.01초)
           → Top N만 GPT-4o mini에 전달 → 최종 매칭 (저렴)
```

**Top 5 vs Top 10 — 어떤 것을 채택할 것인가?**

| 항목 | Top 5 (ChatGPT) | Top 10 (Grok) |
|------|-----------------|---------------|
| 비용 | 더 저렴 | 약간 더 비쌈 |
| 정확도 | 보통 | 더 높음 (놓칠 확률↓) |
| 적합 시점 | 노드 100개 미만 | 노드 150개 이상 |

**Claude 결론: Top 10 채택**
> 노드를 150개 이상으로 확장할 계획이므로, Top 10이 더 안전합니다.
> 비용 차이는 미미하고, 매칭 누락 위험을 줄이는 것이 더 중요합니다.

**Grok 추가 제안 (중요):**
> 프롬프트에 반드시 명시:
> - "관련 노드가 없으면 빈 배열을 반환하라"
> - "relevance 0.3 미만은 제외"
> → AI의 억지 매칭 방지에 핵심적

---

### Q4. node_candidates (미매칭 → 새 노드 생성)

| AI | 판정 | 핵심 의견 |
|----|------|-----------|
| Claude | 5건 이상 누적 시 자동 제안 | 기본 흐름 설계 |
| ChatGPT | ✅ 현실적 + 개선 | 완전 자동화 금지, **주 1회 반자동 배치** |
| Grok | ✅ 현실적 + **구체적 개선** | pgvector 중복 방지 + 3개월 후 자동 승인 고려 |

**ChatGPT 핵심 경고:**
> "AI가 '교통 체증', '차량 정체', '도로 막힘'을 각각 다른 노드로 무한 증식시킬 위험"

**Grok 추가 제안 (채택):**

| 제안 | 내용 | Claude 판정 |
|------|------|-------------|
| raw_text_snippet 컬럼 | 키워드 외에 원본 제보 일부도 저장 → 노드 설명 생성에 활용 | ✅ 채택 |
| pgvector 자동 중복 방지 | 새 키워드 등록 시 기존 후보와 similarity > 0.85이면 report_count만 증가 | ✅ 채택 — 핵심 개선 |
| 3개월 후 자동 승인 | confidence 높은 건 관리자 승인 없이 자동 추가 | ⚠️ 보류 — 3개월 데이터 품질 보고 후 결정 |

**종합 결론: 반자동 + pgvector 중복 방지**
```
매칭 실패 제보 → AI 키워드 추출
→ pgvector로 기존 후보와 비교 (similarity > 0.85 → count만 증가)
→ 새 키워드면 node_candidates에 추가 (raw_text_snippet 포함)
→ 주 1회 배치: AI가 유사 키워드 그룹화 + 대표 노드 이름 제안
→ 관리자(경수님) 승인 → ontology_nodes에 추가 + 벡터 임베딩 생성
```

---

### Q5. 장기 확장성 (Neo4j 마이그레이션)

| AI | 판정 | 핵심 의견 |
|----|------|-----------|
| Claude | 6개월 후 그래프 DB 필요할 수 있음 | 데이터량 기준 |
| ChatGPT | "당분간 잊으셔도 좋습니다" | **쿼리 깊이가 기준**, 데이터량 아님 |
| Grok | "PostgreSQL로 충분히 버틸 수 있습니다" | **구체적 수치 제시** |

**3개 AI 통합 마이그레이션 기준:**

| 기준 | ChatGPT | Grok | 종합 |
|------|---------|------|------|
| 데이터 규모 | 기준 아님 | 노드 8,000+ & 엣지 50,000+ | 참고용 |
| 쿼리 깊이 | 3-4 hop 빈번 시 | 3-hop 쿼리 > 500ms | **핵심 기준** |
| 해결책 (그 전까지) | 인덱스 | **recursive CTE + materialized view** | PostgreSQL 최적화 |

**Grok 추가 지적 (새로운 관점):**
> "Flutter에서 대규모 그래프 시각화 → 300노드 이상 되면 별도 웹뷰로 분리 추천"

**Claude 자체 수정:**
> 내가 "6개월 후 마이그레이션 필요"라고 한 것은 과도한 판단이었습니다.
> PostgreSQL + recursive CTE + materialized view로 수년간 충분합니다.
> 마이그레이션 기준은 '데이터량'이 아니라 '쿼리 깊이(hop 수) × 응답시간'입니다.

---

### Q6. 놓친 고려사항

**3개 AI가 제안한 전체 항목 종합:**

| 항목 | 제안 AI | 중요도 | 실행 시점 | 상세 |
|------|---------|--------|-----------|------|
| **match_reason 컬럼** | ChatGPT | 🔴 높음 | 즉시 | AI가 왜 이 노드와 매칭했는지 1줄 설명 |
| **ai_match_version 컬럼** | Grok | 🟡 중간 | 즉시 | 모델 변경 시 매칭 품질 비교 가능 |
| **verified_count + last_verified_at** | Grok | 🔴 높음 | 즉시 | BOOLEAN 대신 INTEGER — 여러 시민이 검증 가능 |
| **정치적 편향 관리** | Grok | 🔴 높음 | Phase 2 | "좌우 중립적으로 작성하라" 프롬프트 필수 |
| **ai_bias_score 컬럼** | Grok | 🟡 중간 | Phase 3 | 별도 LLM이 편향 평가 (선택적) |
| **악성 제보 필터링** | ChatGPT | 🔴 높음 | Phase 2 | API 앞단에 가벼운 필터링 |
| **Edge 신뢰도 퇴색 (Decay)** | ChatGPT | 🟡 중간 | 장기 | updated_at + 주기적 AI 재평가 |
| **모니터링 대시보드** | Grok | 🟡 중간 | Phase 4 | match rate, avg relevance, verification rate |
| **보안/프라이버시** | Grok | 🔴 높음 | Phase 2 | report_node_links 조회 권한, photo_urls 스토리지 |
| **raw_text_snippet** | Grok | 🟢 낮음 | 즉시 | node_candidates에 원본 텍스트 일부 저장 |

**Grok의 verified_count 제안에 대한 Claude 판단:**
> 원래 `verified_by_user BOOLEAN`으로 설계했는데, Grok의 지적이 맞습니다.
> 3500개 교회 시나리오에서 여러 시민이 같은 매칭을 검증할 수 있어야 합니다.
> `verified_count INTEGER DEFAULT 0` + `last_verified_at TIMESTAMPTZ`로 변경.

**Grok의 정치적 편향 관리에 대한 Claude 판단:**
> 이건 내가 완전히 놓친 부분입니다. 민주AI는 정치 관련 앱이므로,
> 온톨로지 노드가 특정 정치 성향으로 편향되면 앱의 신뢰도가 무너집니다.
> 노드 생성 프롬프트에 "좌우 중립적으로 작성" 지시를 반드시 포함해야 합니다.

---

## 4. 최종 확정 설계 (3개 AI 종합, v2)

### 4-1. 데이터베이스 구조

```
┌──────────────────────────────────────────────────┐
│            순수 지식 그래프 영역                   │
│                                                  │
│  ontology_nodes (30개 → 150~200개 확장 목표)      │
│    + embedding VECTOR(1536)  ← pgvector 신규     │
│                                                  │
│  ontology_edges (29개 → 확장)                     │
│    노드↔노드 관계만                               │
└───────────────────────▲──────────────────────────┘
                        │ (참조만, 혼합 안 함)
┌───────────────────────┴──────────────────────────┐
│            제보-노드 연결 영역                     │
│                                                  │
│  report_node_links (신규)                         │
│    report_id, node_id, relevance,                │
│    verified_count, last_verified_at,             │
│    match_reason, ai_match_version                │
└───────────────────────▲──────────────────────────┘
                        │
┌───────────────────────┴──────────────────────────┐
│            시민 데이터 영역                        │
│                                                  │
│  district_reports (기존)                          │
│    + ontology_status ('pending'|'matched'|        │
│                       'unmatched')               │
│                                                  │
│  node_candidates (신규)                           │
│    keyword, raw_text_snippet, report_count,      │
│    embedding VECTOR(1536), status                │
└──────────────────────────────────────────────────┘
```

### 4-2. 최종 테이블 DDL

```sql
-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. ontology_nodes에 임베딩 컬럼 추가
ALTER TABLE ontology_nodes
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- 3. report_node_links 테이블 (3개 AI 종합)
CREATE TABLE report_node_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES district_reports(id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES ontology_nodes(id) ON DELETE CASCADE,
    relevance FLOAT DEFAULT 0.0,                    -- AI 산출 관련도 (0~1)
    verified_count INTEGER DEFAULT 0,               -- Grok: 여러 시민 검증 가능
    last_verified_at TIMESTAMPTZ,                   -- Grok: 마지막 검증 시각
    match_reason TEXT,                              -- ChatGPT: AI 매칭 이유 설명
    ai_match_version TEXT DEFAULT 'gpt-4o-mini',    -- Grok: 모델 변경 추적
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(report_id, node_id)                      -- 중복 매칭 방지
);

-- 인덱스 (양방향 조회 성능)
CREATE INDEX idx_report_node_links_report ON report_node_links(report_id);
CREATE INDEX idx_report_node_links_node ON report_node_links(node_id);

-- 4. district_reports에 상태 컬럼 추가
ALTER TABLE district_reports
ADD COLUMN IF NOT EXISTS ontology_status TEXT DEFAULT 'pending';

-- 5. node_candidates 테이블 (3개 AI 종합)
CREATE TABLE node_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword TEXT NOT NULL,
    raw_text_snippet TEXT,                          -- Grok: 원본 제보 텍스트 일부
    report_count INTEGER DEFAULT 1,
    embedding vector(1536),                         -- Grok: pgvector 중복 방지용
    status TEXT DEFAULT 'pending',                  -- pending → approved → node_created
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- pgvector 유사도 검색용 인덱스
CREATE INDEX idx_ontology_nodes_embedding
ON ontology_nodes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

CREATE INDEX idx_node_candidates_embedding
ON node_candidates USING ivfflat (embedding vector_cosine_ops) WITH (lists = 5);
```

### 4-3. 매칭 파이프라인 (최종, 3개 AI 종합)

```
시민 제보 제출
    │
    ▼
① district_reports 저장 (즉시, ontology_status='pending')
   → 사용자에게 즉시 응답 (0.5초)
    │
    ▼ (백그라운드 비동기 — FastAPI BackgroundTasks)
② 악성 제보 필터링 (ChatGPT 제안)
    │
    ├── 악성 → ontology_status='filtered', 종료
    │
    ▼
③ text-embedding-3-small로 제보 내용 벡터화
    │
    ▼
④ pgvector 코사인 유사도 → Top 10 후보 노드 검색 (무료, <0.01초)
    │
    ▼
⑤ Top 10 노드 + 제보 → GPT-4o mini 전달
   프롬프트 필수 규칙 (Grok):
   - "관련 노드가 없으면 빈 배열 반환"
   - "relevance 0.3 미만은 제외"
   - "좌우 중립적으로 판단"
    │
    ├── 매칭 성공 → report_node_links에 저장
    │                (relevance, match_reason 포함)
    │                ontology_status = 'matched'
    │
    └── 매칭 실패 → 키워드 추출
                     → pgvector로 기존 후보와 비교 (Grok)
                       ├── similarity > 0.85 → report_count 증가만
                       └── 새 키워드 → node_candidates에 추가
                     ontology_status = 'unmatched'
```

### 4-4. 비용 추정 (월 7만 건 시나리오)

| 항목 | 단가 | 월 비용 |
|------|------|---------|
| text-embedding-3-small (벡터화) | $0.02/1M tokens | ~$2.80 |
| GPT-4o mini (Top 10 매칭) | $0.15/1M input | ~$12.60 |
| pgvector 검색 | Supabase 무료 | $0 |
| Supabase DB | 현재 무료 플랜 | $0 |
| **합계** | | **~$15.40/월** |

※ Claude 원래 설계(전체 노드 프롬프트)였다면: ~$45+/월 (노드 100개 기준)
※ Top 5 대신 Top 10으로 변경해도 비용 차이: ~$2/월 수준

---

## 5. 실행 우선순위 (3개 AI 종합)

### Phase 1: DB 마이그레이션 (즉시)
- [ ] Supabase에 pgvector 확장 활성화
- [ ] ontology_nodes에 embedding 컬럼 추가
- [ ] report_node_links 테이블 생성 (위 DDL)
- [ ] node_candidates 테이블 생성 (위 DDL)
- [ ] district_reports에 ontology_status 컬럼 추가
- [ ] 인덱스 생성

### Phase 2: 서버 핵심 구현
- [ ] 기존 30개 노드 벡터 임베딩 생성 (text-embedding-3-small)
- [ ] pgvector Top 10 검색 함수 구현
- [ ] GPT-4o mini 최종 매칭 함수 구현 (프롬프트 규칙 포함)
- [ ] 비동기 매칭 파이프라인 (BackgroundTasks)
- [ ] 악성 제보 필터링 기본 로직
- [ ] "좌우 중립" 프롬프트 규칙 적용 (Grok)

### Phase 3: 노드 확장 (150~200개)
- [ ] `/api/ontology/generate_batch` 엔드포인트 구현 (Grok)
- [ ] 기존 DB (policy_topics, global_cases, weekly_research) 활용
- [ ] Top 10 분야별 시드 노드 생성
- [ ] 새 노드 벡터 임베딩 생성
- [ ] 새 노드 간 엣지 생성

### Phase 4: 앱 연동 + 모니터링
- [ ] Flutter 앱에서 매칭 결과 표시
- [ ] verified_count 시민 검증 UI
- [ ] 모니터링 대시보드 (Grok 제안):
  - match rate (연결된 제보 비율)
  - average relevance
  - user verification rate
  - new node candidate 생성 속도
- [ ] 주간 node_candidates 관리자 리뷰 기능

---

## 6. 3개 AI 의견 불일치 항목 및 Claude 최종 결정

| 항목 | ChatGPT | Grok | Claude 결정 | 이유 |
|------|---------|------|-------------|------|
| Top N 후보 수 | 5 | 10 | **10** | 150+노드에서 누락 방지가 우선 |
| 목표 노드 수 | ~100 | 150~200 | **150** | 현실적 + 충분한 커버리지 |
| 노드 생성 방법 | 수동 시드 | 배치 엔드포인트 | **배치** | 기존 DB 데이터 활용 가능 |
| verified 타입 | BOOLEAN | INTEGER count | **INTEGER** | 다수 시민 검증 지원 |
| 자동 승인 | 언급 없음 | 3개월 후 고려 | **보류** | 데이터 품질 확인 후 결정 |

---

## 7. 원 설계자(Claude)의 최종 소감

### 내가 틀렸던 것 (솔직히)
1. **프롬프트에 전체 노드 전달** — ChatGPT, Grok 모두 폐기 권고. pgvector가 답.
2. **6개월 후 Neo4j 필요** — 과도한 판단. PostgreSQL + recursive CTE로 수년간 충분.
3. **verified_by_user BOOLEAN** — 단일 사용자 검증만 고려. 다수 검증이 맞음.
4. **정치적 편향 미고려** — 정치 앱에서 이건 치명적 누락. Grok 덕분에 발견.

### 외부 검토에서 얻은 가장 큰 가치
1. **ChatGPT**: pgvector 하이브리드 매칭 — 확장성 병목 완전 해결
2. **Grok**: 정치적 편향 관리 + 구체적 수치 기준 + 실전 운영 관점

### 3개 AI의 공통 결론 (신뢰도 최고)
1. ✅ report_node_links 분리 — 올바른 방향 (만장일치)
2. 🔴 노드 편향 — 가장 시급한 문제 (만장일치)
3. 🔴 매칭 방식 — pgvector 하이브리드로 전환 (만장일치)
4. ✅ PostgreSQL — 당분간 충분, 쿼리 깊이 기준으로 판단 (만장일치)

---

## 8. 현재 Supabase 실제 데이터 현황 (스크린샷 기반)

| 테이블 | 레코드 수 | 상태 |
|--------|-----------|------|
| district_reports | 4건 | 실제 제보 데이터 존재 |
| ontology_nodes | 30건 | 전부 복지 분야 (issue 9, policy 3, global_case 18) |
| ontology_edges | 29건 | 5가지 관계 타입으로 연결됨 |
| report_node_links | 미생성 | Phase 1에서 생성 예정 |
| node_candidates | 미생성 | Phase 1에서 생성 예정 |

---

*이 보고서는 경수님의 요청으로 작성되었습니다.*
*3개 AI의 독립적 검토를 종합하여 최종 설계를 확정했습니다.*
*"천천히 작업을 확실하게 해 놓으면 돼" — 이 원칙을 지키겠습니다.*
