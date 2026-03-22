# 민주AI — Product Requirements Document (PRD)

## v1.0 | 2026.03.22

---

## 1. 제품 개요

| 항목 | 내용 |
|------|------|
| 제품명 | 민주AI |
| 플랫폼 | Android, iOS (Flutter) |
| 백엔드 | FastAPI + Supabase + Railway |
| AI 엔진 | Anthropic Claude API |
| 대상 사용자 | 정치에 관심 있는 대한민국 시민 |
| 핵심 가치 | "근거 있는 정책, 투명한 정치, AI가 24시간 일하는 정당" |

---

## 2. 핵심 기능 요구사항

### 2.1 정책 온톨로지 시스템

#### 2.1.1 데이터베이스 스키마

**테이블: `policy_topics` (52개 분야)**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| week_number | integer | 1~52 (연간 순번) |
| name | text | 분야명 (예: "경제·일자리") |
| description | text | 분야 설명 |
| icon | text | 아이콘 이름 |
| category_group | text | 상위 그룹 (경제/사회/정치/환경) |

**테이블: `weekly_research` (주간 정책 연구)**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| topic_id | uuid | FK → policy_topics |
| year | integer | 연도 |
| week_number | integer | 1~52 |
| cycle | integer | 몇 회전째 (1=첫해, 2=둘째해...) |
| status | text | 'scheduled', 'researching', 'draft', 'review', 'finalized' |
| phase | text | 'mon_select', 'tue_wed_global', 'thu_draft', 'fri_sat_review', 'sun_finalize' |
| korea_status | jsonb | 한국 현황 데이터 |
| global_comparison | jsonb | 글로벌 비교 분석 결과 |
| policy_draft | text | AI 생성 정책안 초안 |
| policy_final | text | 시민 의견 반영 최종안 |
| feasibility_score | float | 실현가능성 점수 (0~100) |
| budget_estimate | text | 예산 추정 |
| expected_effect | text | 예상 효과 |
| citizen_votes_for | integer | 시민 찬성수 |
| citizen_votes_against | integer | 시민 반대수 |
| citizen_comments | integer | 시민 의견수 |
| created_at | timestamptz | 생성일 |
| finalized_at | timestamptz | 확정일 |

**테이블: `ontology_nodes` (지식 그래프 노드)**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| type | text | 'issue', 'policy', 'evidence', 'cause', 'effect', 'stakeholder', 'global_case' |
| name | text | 노드 이름 |
| description | text | 설명 |
| data | jsonb | 노드 유형별 상세 데이터 |
| research_id | uuid | FK → weekly_research (연관 연구) |
| country | text | 국가 코드 (글로벌 사례용) |
| source_url | text | 출처 URL |
| created_at | timestamptz | 생성일 |

**테이블: `ontology_edges` (지식 그래프 관계)**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| from_node_id | uuid | FK → ontology_nodes |
| to_node_id | uuid | FK → ontology_nodes |
| relation_type | text | 'causes', 'solves', 'conflicts_with', 'synergy_with', 'requires', 'affects', 'evidence_for', 'similar_to' |
| strength | float | 관계 강도 (0~1) |
| description | text | 관계 설명 |
| ai_confidence | float | AI 판단 신뢰도 |
| created_at | timestamptz | 생성일 |

**테이블: `global_cases` (글로벌 정책 사례)**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| country | text | 국가 |
| country_code | text | ISO 국가 코드 |
| policy_area | text | 정책 분야 |
| policy_name | text | 정책명 |
| year_started | integer | 시행 연도 |
| description | text | 정책 설명 |
| outcome | text | 결과 ('success', 'partial', 'failure') |
| outcome_detail | text | 상세 결과 |
| key_metrics | jsonb | 핵심 지표 (예: {"unemployment_rate": 4.1}) |
| lessons_learned | text | 교훈 |
| applicability_to_korea | text | 한국 적용 가능성 |
| source_urls | jsonb | 출처 URLs |
| created_at | timestamptz | 생성일 |

**테이블: `citizen_opinions` (시민 의견)**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| research_id | uuid | FK → weekly_research |
| member_id | uuid | FK → members (nullable, 익명 가능) |
| opinion_type | text | 'support', 'oppose', 'modify' |
| content | text | 의견 내용 |
| ai_summary | text | AI가 요약한 핵심 |
| created_at | timestamptz | 생성일 |

**테이블: `agent_activities` (에이전트 활동 로그)**
| 필드 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| agent_id | text | 에이전트 ID |
| action | text | 수행한 작업 |
| detail | text | 상세 내용 |
| status | text | 'success', 'error', 'running' |
| result_summary | text | 결과 요약 |
| metadata | jsonb | 추가 데이터 |
| created_at | timestamptz | 생성일 |

---

### 2.2 앱 화면 구조

#### 화면 1: AI 컨트롤 센터 (홈)

**목적:** 앱을 여는 순간 "7개 AI가 일하고 있다"를 체감

**구성 요소:**
1. **상단 헤더**
   - "🟢 7개 에이전트 가동 중 | {uptime_days}일째 무중단"
   - "오늘 처리 작업: {today_tasks}건"

2. **AI 일일 브리핑 카드**
   - 오케스트레이터가 매일 08:00 자동 생성
   - 오늘의 주요 이슈, 에이전트 활동 요약
   - 생성 시각 표시

3. **이번 주 정책 연구 카드**
   - 현재 연구 중인 분야 + 진행 단계 (월~일)
   - 글로벌 비교 미리보기
   - "참여하기" 버튼 (금~토 토론 기간)

4. **에이전트 상태 바**
   - 7개 에이전트 아이콘 가로 배열
   - 각 에이전트 마지막 활동 시간 표시
   - 실시간 대기 중인 에이전트는 🟢 표시

5. **실시간 활동 피드**
   - 시간순 에이전트 활동 로그 (최근 10건)
   - 예: "14:00 📊 분석 — 당원 +3명 증가 감지"

**API 호출:**
- `GET /api/agents/live` — 에이전트 실시간 상태
- `GET /api/agents/activity` — 활동 피드
- `GET /api/briefing/today` — 오늘의 브리핑
- `GET /api/research/current` — 이번 주 연구 현황

---

#### 화면 2: 정책 탭 (전면 개편)

**목적:** 정책 온톨로지 탐색 + 주간 연구 아카이브 + 시민 참여

**구성 요소:**
1. **이번 주 정책 연구** (상단 하이라이트)
   - 분야, 진행 단계, 글로벌 비교 미리보기
   - 토론 기간이면 의견 입력 UI

2. **정책 아카이브** (지난 연구 목록)
   - 주차별 카드 (분야 아이콘 + 제목 + 실현가능성 점수)
   - 터치 → 상세 화면 (한국 현황, 글로벌 비교, 정책안, 시민 의견)

3. **정책 지도** (온톨로지 시각화)
   - 분야 간 연결 관계를 노드 그래프로 표시
   - 터치하면 관련 정책·원인·효과 펼쳐짐
   - 연결선 굵기 = 영향력 크기

4. **시민 정책 제안**
   - 제안 → 즉시 AI 분석 (실현가능성, 글로벌 사례)
   - 유사 기존 정책 자동 매칭

**API 호출:**
- `GET /api/research/current` — 이번 주 연구
- `GET /api/research/archive` — 지난 연구 목록
- `GET /api/research/{id}` — 연구 상세
- `GET /api/ontology/map` — 정책 지도 데이터
- `GET /api/ontology/node/{id}` — 노드 상세
- `POST /api/research/{id}/opinion` — 시민 의견 제출
- `POST /api/policies/propose` — 정책 제안 + AI 분석

---

#### 화면 3: AI 챗봇 (솔루션 엔진 통합)

**목적:** 모든 정책 질문에 온톨로지 기반 근거 있는 답변

**구성 요소:**
1. **대화 영역**
   - 유저 메시지 + AI 응답
   - AI 응답에 "호출된 에이전트" 표시 (예: 👁 모니터링 + 📋 정책)
   - 근거 데이터 인라인 표시

2. **에이전트 라우팅 표시**
   - "🔄 오케스트레이터가 분석 중..."
   - "👁 모니터링 에이전트 호출"
   - "📋 정책 에이전트 호출"
   - → 유저가 뒤에서 여러 에이전트가 협업하는 걸 시각적으로 확인

3. **솔루션 응답 포맷**
   - 문제 정의 (데이터 기반)
   - 글로벌 사례 (국기 + 국가명 + 결과)
   - AI 솔루션 (단기/중기/장기)
   - 실현가능성 점수 + 예산
   - [정책 지도에서 보기] 버튼

4. **대화 히스토리**
   - 로컬 저장 + API 전송
   - 맥락 유지 (이전 대화 참조)

**API 호출:**
- `POST /api/chat/smart` — 온톨로지 기반 스마트 챗 (에이전트 라우팅 포함)

---

#### 화면 4: AI 에이전트 탭

**목적:** 7개 에이전트가 24시간 일하는 것을 상세하게 보여줌

**구성 요소:**
1. **에이전트 대시보드 헤더**
   - 총 에이전트 수, 가동 일수, 오늘 작업수

2. **에이전트 카드 (7개)**
   - 에이전트 이름, 역할, 상태
   - 마지막 활동 시간, 오늘 처리 건수
   - 다음 예정 작업 + 시간
   - 터치 → 에이전트 상세 화면

3. **에이전트 상세 화면** (각 에이전트별)
   - 실시간 데이터 표시 (에이전트별 다른 UI)
   - 활동 이력 (최근 7일)
   - "이 에이전트에게 물어보기" (챗 연동)

4. **24시간 스케줄 표**
   - 타임라인 형태로 에이전트별 작업 시간 표시

**API 호출:**
- `GET /api/agents/live` — 에이전트 실시간 상태
- `GET /api/agents/{id}/detail` — 에이전트 상세
- `GET /api/agents/activity` — 활동 피드
- `GET /api/agents/schedule` — 24시간 스케줄

---

#### 화면 5: 내 정보 탭

**목적:** 개인화 + 지역구 연결 + 참여 이력

**구성 요소:**
1. **프로필**
   - 이름, 이메일, 관심 지역구 설정
   - 관심 정책 분야 선택 (최대 5개)

2. **내 지역구 모니터링**
   - 설정한 지역구의 현 의원 정보
   - 출석률, 공약 이행률, 취약도 점수
   - 해당 지역 맞춤 정책 추천

3. **참여 이력**
   - 정책 투표 이력
   - 제출한 의견
   - 활동 점수 (민주주의 참여 지수)

4. **알림 설정**
   - 주간 정책 알림 on/off
   - 내 지역구 의원 활동 알림 on/off
   - AI 브리핑 알림 on/off

---

### 2.3 백엔드 API 요구사항

#### 신규 API 엔드포인트

**정책 연구 사이클:**
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/research/current` | 이번 주 진행 중인 연구 |
| GET | `/api/research/archive` | 완료된 연구 목록 (페이지네이션) |
| GET | `/api/research/{id}` | 연구 상세 (한국 현황 + 글로벌 비교 + 정책안) |
| POST | `/api/research/{id}/opinion` | 시민 의견 제출 |
| GET | `/api/research/{id}/opinions` | 시민 의견 목록 |

**온톨로지:**
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/ontology/map` | 전체 지식 그래프 (노드 + 엣지) |
| GET | `/api/ontology/node/{id}` | 노드 상세 + 연결된 노드들 |
| GET | `/api/ontology/search?q=` | 온톨로지 검색 |
| GET | `/api/ontology/related/{issue}` | 특정 이슈와 관련된 모든 정책·원인·효과 |

**글로벌 비교:**
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/global/cases?area=` | 분야별 글로벌 사례 |
| GET | `/api/global/compare?issue=` | 특정 이슈 글로벌 비교 분석 |

**에이전트 (강화):**
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/agents/live` | 7개 에이전트 실시간 상태 |
| GET | `/api/agents/{id}/detail` | 에이전트 상세 + 최근 활동 |
| GET | `/api/agents/activity` | 전체 활동 피드 (최근 30건) |
| GET | `/api/agents/schedule` | 24시간 스케줄표 |

**브리핑:**
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/briefing/today` | 오늘의 AI 브리핑 |
| GET | `/api/briefing/archive` | 과거 브리핑 목록 |

**스마트 챗:**
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat/smart` | 온톨로지 기반 스마트 챗 (에이전트 라우팅) |

**선거:**
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/election/dashboard` | 선거 대시보드 (D-day, 지지율, 목표 진행률) |
| GET | `/api/election/districts` | 타겟 지역구 현황 |

---

### 2.4 신규/강화 에이전트

#### 🆕 PolicyResearchAgent (정책 연구원)
기존 PolicyAgent 대폭 강화

**역할:** 주간 정책 자동 연구 사이클 실행
**주요 메서드:**
- `start_weekly_research(week_number)` — 주간 연구 시작
- `research_korea_status(topic)` — 한국 현황 조사
- `research_global_comparison(topic)` — 글로벌 비교 분석
- `generate_policy_draft(research_id)` — 정책안 초안 생성
- `finalize_policy(research_id, citizen_opinions)` — 최종안 확정
- `update_ontology(research_id)` — 온톨로지에 새 노드/엣지 추가

**스케줄:**
- 월 00:00 — `start_weekly_research()`
- 화 00:00 — `research_global_comparison()`
- 목 00:00 — `generate_policy_draft()`
- 일 22:00 — `finalize_policy()`

#### 🆕 GlobalComparisonAgent (글로벌 비교 분석가)
PolicyResearchAgent의 서브 에이전트로 작동

**역할:** 전세계 정책 사례 수집·분석·비교
**주요 메서드:**
- `search_global_cases(topic, countries)` — 해외 사례 검색
- `compare_policies(korea_status, global_cases)` — 비교 분석
- `evaluate_applicability(case, korea_context)` — 한국 적용 가능성 평가
- `find_best_practices(topic)` — 최선 사례 추출

#### 🆕 SolutionEngine (솔루션 엔진)
챗봇과 통합 작동

**역할:** 시민 질문 → 근거 기반 해법 도출
**주요 메서드:**
- `analyze_question(question)` — 질문 분석 + 온톨로지 검색
- `find_related_policies(question)` — 관련 정책 검색
- `find_global_solutions(issue)` — 글로벌 해법 검색
- `generate_solution(question, context)` — 단기/중기/장기 솔루션 생성
- `route_to_agents(question)` — 적절한 에이전트에 라우팅

---

## 3. 구현 우선순위

### Phase 1: 기반 구축 (즉시)
1. Supabase 온톨로지 DB 스키마 생성
2. 52개 정책 분야 시드 데이터 입력
3. 에이전트 활동 로그 테이블 + API
4. 에이전트 실시간 상태 API

### Phase 2: 주간 정책 사이클 (1주차)
5. PolicyResearchAgent 구현
6. 글로벌 비교 분석 기능
7. 주간 연구 API 엔드포인트
8. 시민 의견 API

### Phase 3: 앱 UI 개편 (1주차)
9. 홈 화면 → AI 컨트롤 센터
10. 에이전트 탭 → 실시간 대시보드
11. 정책 탭 → 주간 연구 + 아카이브
12. 챗봇 → 에이전트 라우팅 + 솔루션

### Phase 4: 온톨로지 시각화 (2주차)
13. 정책 지도 UI (노드 그래프)
14. 솔루션 엔진 통합
15. 선거 대시보드

### Phase 5: 고도화 (3주차~)
16. 푸시 알림 (FCM)
17. 텔레그램 봇 연동
18. 온톨로지 자동 확장
19. 실시간 SNS 연동

---

## 4. 성공 지표

| 지표 | 3개월 | 6개월 | 1년 |
|------|-------|-------|-----|
| 앱 다운로드 | 1,000 | 5,000 | 20,000 |
| 월간 활성 사용자 | 300 | 1,500 | 8,000 |
| 정책 아카이브 | 12개 | 26개 | 52개 |
| 온톨로지 노드 | 100 | 300 | 800 |
| 시민 의견 | 500 | 3,000 | 15,000 |
| 당원 | 200 | 1,000 | 5,000 |
| 글로벌 사례 DB | 50 | 150 | 400 |

---

## 5. 비기능 요구사항

| 항목 | 요구 수준 |
|------|-----------|
| 응답 속도 | API < 3초, 챗봇 < 10초 |
| 가용성 | 99.5% uptime |
| 보안 | HTTPS, 개인정보 암호화 |
| 확장성 | 동시 접속 1,000명 지원 |
| 비용 | AI API 월 $100 이내 (Batch + Caching 최적화) |

---

*작성: AI 정당 시스템 | 2026.03.22*
*이 문서는 살아있는 문서로, 주기적으로 업데이트됩니다.*
