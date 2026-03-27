# 민주AI 온톨로지 시스템 — 전체 리뷰 리포트

**작성자**: Claude Opus 4.6 (Anthropic)
**작성일**: 2026-03-27
**목적**: 다른 AI(GPT-4o, Gemini 등)에게 검증 및 개선 의견을 구하기 위한 기술 리포트
**프로젝트**: 민주AI — 세계 최초 AI 운영 정당 앱

---

## 1. 프로젝트 배경

### 1.1 민주AI란?
- 시민이 국회의원을 감시하고, AI가 정책을 연구하는 정당 앱
- Flutter 앱 (Android/iOS) + FastAPI 백엔드 (Railway) + Supabase PostgreSQL
- 대한민국 국회 295명 의원 + 25,337건 법안 데이터 보유
- 목표: 3,500개 교회 청년 참여 → 2028 총선 10석

### 1.2 온톨로지의 역할
- 시민 제보, 정책, 이슈, 해외 사례를 **지식 그래프**로 연결
- "노인 요양원 부족 제보" → "노인복지 부족" 이슈 → "일본 고령자 복지" 해외 사례 연결
- 장기적으로 Palantir 수준의 정치 지식 그래프 구축이 비전

---

## 2. 실수 이력 (정직한 기록)

### 2.1 1차 실수: 가짜 온톨로지 (2026-03-22, Sonnet 4.6 작업)

**무엇을 했나:**
```sql
-- migrations/009_ontology_tags.sql
ALTER TABLE district_reports ADD COLUMN ontology_tags JSONB DEFAULT '{}';
ALTER TABLE proposals ADD COLUMN ontology_tags JSONB DEFAULT '{}';
```

**왜 잘못인가:**
- JSONB 컬럼 하나에 AI가 생성한 태그를 넣는 것은 **온톨로지가 아님**
- 이건 그냥 "AI 메타데이터" — 노드도 없고, 엣지도 없고, 그래프도 없음
- `ontology_tags`라는 이름이 사용자에게 "온톨로지를 구현했다"는 거짓 인상을 줌
- 같은 패턴이 고향마켓(다른 앱)에도 적용됨

**서버 코드에서도 잘못됨:**
```python
# main.py에 추가했던 코드 (삭제됨)
async def _create_ontology_from_report(report_data):
    # GPT가 태그를 생성해서 JSONB에 넣는 로직
    # → 이건 ontology_nodes/edges와 무관한 별도 시스템
```

**피해 범위:**
- Supabase: district_reports, proposals 테이블에 컬럼 추가됨
- 서버: main.py에 가짜 온톨로지 코드 추가됨
- Flutter 앱: 4개 파일에 관련 UI 코드 추가됨
- 고향마켓: 같은 패턴 적용됨

### 2.2 수정 작업 (2026-03-26, Opus 4.6)

**되돌린 것:**
1. `git revert c7e88f0` — 서버 코드 원상복구, Railway 자동 재배포
2. Supabase SQL Editor에서 직접 실행:
   ```sql
   ALTER TABLE district_reports DROP COLUMN IF EXISTS ontology_tags;
   ALTER TABLE proposals DROP COLUMN IF EXISTS ontology_tags;
   ```
3. Flutter 앱: 4개 파일 원상복구, GitHub에 push (`nanoset100/minjuai-app`)
4. 고향마켓: `ontologyTags` → `aiMetadata`로 이름 변경 (메타데이터로 솔직하게 사용)

---

## 3. 현재 상태 (2026-03-27 기준)

### 3.1 DB 테이블 구조

**ontology_nodes** (30개 노드):
```sql
CREATE TABLE ontology_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL CHECK (type IN ('issue', 'policy', 'evidence', 'cause', 'effect', 'stakeholder', 'global_case')),
    name TEXT NOT NULL,
    description TEXT,
    data JSONB DEFAULT '{}',
    research_id UUID REFERENCES weekly_research(id),
    country TEXT,
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

노드 분포:
| type | 개수 | 예시 |
|------|------|------|
| issue | 9 | 고령화 복지 부담, 저출산 문제, 소득 불평등, 청년 실업 등 |
| policy | 3 | 포괄적 복지 시스템, 통합 복지 증진, 포용적 복지 시스템 |
| global_case | 18 | 스웨덴 복지, 일본 고령자 복지, 독일 연금 개혁 등 |

**심각한 편향**: 30개 노드 전부가 **복지** 분야. 52개 정책 분야 중 1개만 커버.

**전체 30개 노드 목록 (Supabase 실제 데이터 기준):**

issue 노드 (9개):
| name | description | country |
|------|-------------|---------|
| 저출산으로 인한 인력 부족 | 저출산은 노동력 감소 & 복지 부담 증가 | KR |
| 고령화 사회 대응 | 고령 인구가 증가하고 있어 노인 복지 서비스 필요 | KR |
| 노인복지 부족 | 고령 인구 증가에 따른 복지 서비스 부족 및 돌봄 문제 | KR |
| 고령화에 따른 복지 부담 증가 | 고령자가 증가함에 따라 기초연금과 의료비 등 부담 | KR |
| 지역 간 복지 격차 | 도시와 지방 간 복지 수준 차이로 인한 불평등 | KR |
| 사회적 불평등 확대 | 소득 및 자산 불평등이 심화되면서 복지 정책 필요 | KR |
| 소득 불평등 | 소득계층 간 격차가 커지고 있어 사회적 불안정 | KR |
| 청년 실업 및 주거 문제 | 청년층의 높은 실업률과 주거 비용 상승으로 고통 | KR |
| 저출산 문제 | 저출산율로 인한 미래 노동력 감소와 복지 부담 증가 | KR |

policy 노드 (3개):
| name | description |
|------|-------------|
| 포괄적 복지 시스템 구축 | 고령화와 저출산 문제를 해결하기 위한 포괄적 복지 |
| 통합 복지 증진 정책 | 정책안은 한국의 노인복지와 저출산 문제를 종합 포함 |
| 포용적 복지 시스템 구축 | 청년·저소득층 집중 지원 정책 |

global_case 노드 (18개):
| name | country | outcome |
|------|---------|---------|
| 노르웨이 - 노동자 복지 정책 | NO | success |
| 핀란드 - 기본 소득 실험 | FI | partial |
| 스웨덴 - 보편적 복지 모델 | SE | success |
| 핀란드 - 기초소득 실험 | FI | partial |
| 독일 - 구직자 수당 | DE | success |
| 스웨덴 - 사회 복지 국가 모델 | SE | success |
| 프랑스 - 최저임금 인상 정책 | FR | partial |
| 독일 - 연금 개혁 프로그램 | DE | partial |
| 일본 - 고령자 복지정책 | JP | failure |
| 영국 - 보편적 기본 소득 실험 | GB | failure |
| 스웨덴 - 사회복지 시스템 | SE | success |
| 캐나다 - 주 정부 주도의 의료 시스템 | CA | success |
| 미국 - Medicaid | US | partial |
| 일본 - 노인 복지 증진 정책 | JP | failure |
| 독일 - 사회적 보호법 | DE | success |
| 영국 - NHS (국민보건서비스) | GB | success |
| 영국 - 복지 축소 정책 | GB | failure |
| 핀란드 - 기초소득 사법산업 | FI | partial |

**참고**: 모든 노드가 동일한 research_id(6ca57365-...)를 공유 → 하나의 주간연구에서 일괄 생성됨
**참고**: data JSONB에 outcome, key_metric, label 등 메타데이터 포함

**ontology_edges** (29개 엣지):
```sql
CREATE TABLE ontology_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_node_id UUID REFERENCES ontology_nodes(id) ON DELETE CASCADE,
    to_node_id UUID REFERENCES ontology_nodes(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL CHECK (relation_type IN ('causes', 'solves', 'conflicts_with', 'synergy_with', 'requires', 'affects', 'evidence_for', 'similar_to')),
    strength FLOAT DEFAULT 0.5 CHECK (strength BETWEEN 0 AND 1),
    description TEXT,
    ai_confidence FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

엣지 분포:
| relation_type | 개수 | 의미 |
|---------------|------|------|
| solves | 7 | 정책→이슈 해결 |
| causes | 4 | 이슈→이슈 원인 |
| similar_to | 4 | 이슈↔이슈 유사 |
| evidence_for | 12 | 해외사례→정책/이슈 근거 |
| synergy_with | 2 | 정책↔정책 시너지 |

**전체 29개 엣지 목록 (Supabase 실제 데이터 기준):**

solves (7개 — 정책이 이슈를 해결):
| from (policy) | to (issue) | strength | description |
|---------------|------------|----------|-------------|
| 포괄적 복지 시스템 구축 | 고령화에 따른 복지 부담 증가 | 0.8 | 포괄적 복지로 고령화 복지 부담 해결 |
| 포괄적 복지 시스템 구축 | 저출산으로 인한 인력 부족 | 0.7 | 아동수당 등으로 저출산 문제 대응 |
| 포괄적 복지 시스템 구축 | 사회적 불평등 확대 | 0.7 | 사회적 불평등 해소 목적 포함 |
| 통합 복지 증진 정책 | 노인복지 부족 | 0.9 | 노인복지 개편이 핵심 목적 |
| 통합 복지 증진 정책 | 저출산 문제 | 0.7 | 저출산 문제 종합 해결 포함 |
| 포용적 복지 시스템 구축 | 청년 실업 및 주거 | 0.9 | 청년·저소득층 집중 지원 정책 |
| 포용적 복지 시스템 구축 | 소득 불평등 | 0.8 | 소득 불평등 해결이 핵심 목적 |

causes (4개 — 이슈가 이슈를 야기):
| from (issue) | to (issue) | strength | description |
|--------------|------------|----------|-------------|
| 저출산 문제 | 고령화 복지 부담 증가 | 0.9 | 저출산이 고령화를 가속시켜 복지 부담 증가 |
| 사회적 불평등 확대 | 지역 간 복지 격차 | 0.8 | 사회적 불평등이 지역 간 격차로 이어짐 |
| 소득 불평등 | 청년 실업 및 주거 문제 | 0.7 | 소득 격차가 청년층 주거 문제를 악화 |
| 저출산으로 인한 인력 부족 | 고령화 사회 대응 | 0.8 | 인력 부족이 고령화 대응을 더 시급하게 만듦 |

similar_to (4개 — 유사 이슈):
| node A | node B | strength |
|--------|--------|----------|
| 고령화 복지 부담 증가 | 고령화 사회 대응 | 0.9 |
| 저출산으로 인한 인력 부족 | 저출산 문제 | 0.9 |
| 사회적 불평등 확대 | 소득 불평등 | 0.85 |
| 노인복지 부족 | 고령화 사회 대응 | 0.85 |

evidence_for (12개 — 해외사례가 근거 제공):
| from (global_case) | to (policy/issue) | strength |
|--------------------|-------------------|----------|
| 스웨덴 보편적 복지 | 포괄적 복지 시스템 | 0.85 |
| 스웨덴 사회복지 시스템 | 통합 복지 증진 정책 | 0.8 |
| 핀란드 기본소득 실험 | 통합 복지 증진 정책 | 0.75 |
| 일본 고령자 복지 | 고령화 사회 대응 | 0.8 |
| 일본 노인 복지 증진 | 노인복지 부족 | 0.8 |
| 독일 연금 개혁 | 노인복지 부족 | 0.75 |
| 영국 복지 축소 | 사회적 불평등 확대 | 0.85 |
| 독일 사회적 보호법 | 소득 불평등 | 0.7 |
| 프랑스 최저임금 | 소득 불평등 | 0.7 |
| 독일 구직자 수당 | 청년 실업 및 주거 | 0.7 |
| 노르웨이 노동자 복지 | 포용적 복지 시스템 | 0.7 |
| 캐나다 의료 시스템 | 포괄적 복지 시스템 | 0.7 |

synergy_with (2개 — 정책 간 시너지):
| policy A | policy B | strength | description |
|----------|----------|----------|-------------|
| 포괄적 복지 시스템 | 통합 복지 증진 정책 | 0.8 | 서로 보완하여 복지 확대 |
| 통합 복지 증진 정책 | 포용적 복지 시스템 | 0.75 | 노인·청년 복지가 함께 작동해야 효과적 |

**district_reports** (4건 실제 데이터):
```sql
CREATE TABLE district_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL,
    mona_cd TEXT NOT NULL,
    report_type TEXT NOT NULL CHECK (report_type IN ('현안', '사진', '기사', '평가', '공약', '예산')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    news_url TEXT,
    photo_urls JSONB DEFAULT '[]',
    user_name TEXT DEFAULT '익명 시민',
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    status TEXT DEFAULT 'published',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

실제 제보 데이터:
| district | report_type | title |
|----------|-------------|-------|
| 광주 북구갑 | 현안 | 예산낭비 (해외 출장에 산 과다 지출) |
| 성남시 분당구 갑 | 기사 | 사업확장 의혹 (국회의원 신분 이용) |
| 서울 노원구갑 | 현안 | 도로 보수 미비 제보 |
| 성남시 분당구 갑 | 현안 | 세비 낭비 (지역구 활동 전혀 안 함) |

**현재 district_reports와 ontology_nodes 사이에 연결이 전혀 없음.**

### 3.2 서버 API 현황

```
GET  /api/ontology/map     → 전체 노드+엣지 반환 (작동 중)
GET  /api/ontology/search  → 이름으로 노드 검색 (작동 중)
POST /api/districts/report → 시민 제보 등록 (온톨로지와 무관)
```

### 3.3 관련 테이블 전체 목록 (Supabase 확인)

```
agent_activities, citizen_opinions, citizen_point_logs, citizen_points,
conversations, district_ratings, district_reports, global_cases,
lawmakers, members, ontology_edges, ontology_nodes, policy_topics,
proposals, push_tokens, votes, weekly_research
```

---

## 4. 설계 과정 (3단계 진화)

### 4.1 1차 설계안 (결함 있음)

```
district_reports 테이블에 linked_node_ids UUID[] 추가
+ ontology_edges에 reported_about 관계 추가
```

**자체 발견한 결함:**
1. **구조적 모순**: ontology_edges의 from_node_id/to_node_id는 ontology_nodes.id를 참조함. district_reports의 id는 ontology_nodes에 없으므로 엣지 생성 불가
2. **중복 저장**: linked_node_ids와 edges 양쪽에 같은 데이터
3. **매칭 불가 미고려**: 복지 외 분야 제보는 연결할 노드 없음

### 4.2 2차 설계안 (개선)

```
별도 연결 테이블 report_node_links 생성
ontology 그래프는 오염시키지 않음
```

**자체 발견한 약점:**
1. AI 매칭 품질 검증 수단 없음
2. 30개 중 매칭 가능한 노드 실질 12개 (issue 9 + policy 3)
3. 비동기 처리 설계 누락 (GPT 호출 시 사용자 대기)

### 4.3 3차 설계안 (현재 최종안)

```
┌─────────────────┐
│ ontology_nodes  │  30개 (순수 지식 그래프)
│ ontology_edges  │  29개 (노드 간 관계만)
└────────▲────────┘
         │ (참조만, 혼합 안 함)
┌────────┴────────┐
│ report_node_links│  새 테이블
│ - report_id     │  → district_reports.id
│ - node_id       │  → ontology_nodes.id
│ - relevance     │  0~1 (AI 산출)
│ - verified_by_user│ BOOLEAN (시민 확인)
│ - created_at    │
└────────▲────────┘
         │
┌────────┴────────┐
│ district_reports│  4건 (+ ontology_status 추가)
│ + ontology_status│ 'pending'|'matched'|'unmatched'
└─────────────────┘

┌─────────────────┐
│ node_candidates │  새 테이블 (미매칭 키워드 수집)
│ - keyword       │  "교통 체증", "학교 급식" 등
│ - report_count  │  누적 횟수
│ - status        │ 'pending'|'approved'|'node_created'
└─────────────────┘
```

**핵심 특징:**
1. **온톨로지 그래프 순수성 유지** — 시민 데이터가 지식 그래프를 오염시키지 않음
2. **시민 검증** — AI 매칭 후 사용자가 확인/수정 가능
3. **비동기 처리** — 제보 즉시 저장, GPT 매칭은 백그라운드
4. **유기적 성장** — 미매칭 제보에서 새 노드 후보 자동 수집
5. **매칭 실패 허용** — 관련 노드 없으면 연결 0개도 정상

---

## 5. 알려진 문제점 및 위험

### 5.1 노드 편향 문제 (Critical)
- 30개 노드가 전부 **복지** 관련
- 52개 정책 분야 중 복지 1개만 커버
- 시민 제보의 절반 이상이 매칭 불가일 수 있음
- 실제 4건 제보 중 "도로 보수 미비"는 교통 분야 → 매칭 불가

### 5.2 스케일 문제 (Medium)
- 현재: 30 노드 + 29 엣지 → PostgreSQL 충분
- 3,500교회 시나리오: 월 7만 건 제보 예상
  - report_node_links: 7만 × 평균 2개 매칭 = 월 14만 행
  - 6개월이면 84만 행 → PostgreSQL 인덱스로 충분히 처리 가능
  - 노드가 1,000개 이상이면 그래프 탐색 성능 문제 → 그때 Neo4j 고려

### 5.3 AI 매칭 신뢰도 (Medium)
- GPT-4o mini의 노드 매칭 정확도는 테스트 전까지 알 수 없음
- 억지 매칭 위험: "뭐라도 골라야 한다"고 AI가 판단할 수 있음
- 완화책: verified_by_user 필드 + 관련 노드 없음도 허용

### 5.4 비용 (Low)
- GPT-4o mini: 제보 1건당 ~$0.001
- 월 7만 건: ~$70/월 → 허용 범위

---

## 6. 검증 요청 사항

다른 AI에게 다음 질문에 대한 의견을 요청합니다:

### Q1. 아키텍처 적절성
- report_node_links 별도 테이블 방식이 맞는가?
- 아니면 제보를 ontology_nodes에 넣어야 하는가? (노드 타입 'report' 추가)
- 더 나은 대안이 있는가?

### Q2. 노드 편향 해결 전략
- 현재 복지만 30개. 52개 분야로 확장하려면?
- 한 번에 확장? 점진적 확장? AI 자동 생성?
- 초기 시드 노드의 적절한 규모는?

### Q3. AI 매칭 프롬프트 설계
- 30개(이후 수백 개) 노드 목록을 GPT에게 주고 매칭시키는 방식이 최선인가?
- 임베딩 벡터 유사도 검색이 더 나은가?
- 하이브리드 접근이 필요한가?

### Q4. node_candidates (미매칭 → 새 노드) 설계
- 키워드 수집 → 관리자 승인 → 노드 생성 흐름이 현실적인가?
- 자동화 수준은 어디까지가 적절한가?
- 중복/유사 키워드 병합은 어떻게?

### Q5. 장기 확장성
- PostgreSQL → Neo4j 마이그레이션 시점과 기준은?
- node/edge 구조가 그래프 DB로 1:1 전환 가능한 설계인가?
- 3,500개 교회(약 7만 월간 사용자) 규모에서의 병목은 어디인가?

### Q6. 놓친 것이 있는가?
- 이 설계에서 놓치고 있는 중요한 고려사항은?
- 보안, 프라이버시, 데이터 품질 등 검토 필요한 부분은?

---

## 7. 기술 스택 요약

| 구성요소 | 기술 | 상태 |
|----------|------|------|
| 앱 | Flutter (Dart) | 운영 중 |
| 백엔드 | Python FastAPI | Railway 배포 중 |
| DB | Supabase PostgreSQL | 운영 중 |
| AI | OpenAI GPT-4o mini | 운영 중 ($0.15/1M input) |
| 온톨로지 저장 | ontology_nodes + ontology_edges | 30노드 + 29엣지 |
| 시민 제보 | district_reports | 4건 |
| 제보↔온톨로지 연결 | 미구현 | 설계 완료, 검증 대기 |

---

## 8. 이 리포트를 검증하는 AI에게

이 프로젝트의 핵심 제약 조건:
1. **1인 개발** — 복잡한 아키텍처 유지 어려움
2. **예산 제한** — 월 $100 이하 운영비 (Railway + Supabase + OpenAI)
3. **PostgreSQL 기반** — 전용 그래프 DB 사용 불가 (현 단계)
4. **실제 운영 중인 앱** — 실험이 아님, 실제 시민이 사용 중
5. **장기 비전** — 3,500개 교회 청년 참여, 2028 총선 도전

**솔직한 자기 평가**: 최초 가짜 온톨로지(JSONB 태그) 실수를 인정합니다. 현재 설계는 3차 반복 개선을 거쳤지만, 아직 구현 전이므로 검증과 개선의 여지가 있습니다. 특히 노드 편향 문제(복지만 30개)와 AI 매칭 품질은 외부 전문가의 의견이 필요합니다.
