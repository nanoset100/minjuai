# Phase 4 실행계획서: Flutter 앱 온톨로지 연동

**작성일**: 2026-03-29
**작성자**: Claude Opus (앱 총책임자)
**검토자**: Grok (xAI), Claude Sonnet (Anthropic), Gemini (Google) — 3개 AI 크로스 리뷰 완료

---

## 총책임자 평가: 3개 AI 피드백 리뷰

### 각 AI 피드백 품질 평가

| AI | 점수 | 강점 | 약점 |
|----|------|------|------|
| **Grok** | 8.5/10 | MVP 우선순위 명확, BottomSheet UX 구체적, 실행 가능한 조언 | Dio 전환 추천은 현재 단계에서 과도, 백엔드 RLS는 MVP에서 불필요한 공수 |
| **Claude Sonnet** | 9/10 | relevance 임계값 이슈 발견 (Critical), 한글 인코딩 지적, SnackBar 액션 UX 가장 자연스러움 | A안 폴링(5초 1회)은 너무 소극적, 오프라인 큐는 우선순위 낮음 |
| **Gemini** | 7.5/10 | JSON 타입 안전 변환 지적 유용, 텍스트 오버플로우 실전 팁 | Step 4를 먼저 하자는 순서 변경 근거 약함, 상태관리 A안(setState) 추천은 비효율적 |

### 가장 가치 있었던 피드백 Top 3

1. **Sonnet — relevance 0.32~0.40 이슈 발견 (Critical)**
   내가 완전히 놓친 부분. 현재 DB의 실제 매칭 점수가 전부 낮은데, 이걸 그대로 보여주면 "AI가 엉터리"라는 첫인상을 줌. 이 발견 하나만으로도 외부 리뷰의 가치가 증명됨.

2. **Grok — BottomSheet에서 폴링하며 실시간 업데이트하는 UX**
   "AI가 분석 중..." → "매칭 완료!" 로 Sheet 내용이 바뀌는 경험은 사용자에게 "AI가 진짜 일하고 있다"는 인식을 강하게 줌. Sonnet의 SnackBar 액션 아이디어와 결합하면 최고의 UX.

3. **Gemini — `(json['relevance'] as num).toDouble()` 타입 안전 변환**
   사소해 보이지만 이게 실제 배포 후 크래시의 1순위 원인. Python은 int/float 자동 변환하지만 Dart는 엄격함. 이것 때문에 앱이 터지는 경우가 매우 흔함.

### 내가 원래 계획에서 틀렸던 것

1. **Step 2와 3을 분리 구현하려 했음** → 3개 AI 모두 "같은 UI에 넣어라" → 맞음, 분리하면 어중간
2. **relevance 임계값을 고려하지 않았음** → 매칭 점수를 그냥 보여주면 역효과
3. **embedding 제외를 "확인 필요" 수준으로 넘겼음** → 1.4MB는 모바일에서 치명적, 반드시 선제 처리

### 내가 원래 계획에서 맞았던 것

1. **Step 1→2→3→4→5 기본 순서** — Gemini만 Step 4 선행 주장, 나머지 2개 AI 동의
2. **C안 (HomeScreen 서브화면)** — 3/3 만장일치
3. **MVP 먼저 선언하고 확장** — 3/3 만장일치

### 솔직한 자기 평가

원래 내 계획은 **7.5점** 수준이었음.
- 큰 방향은 맞았지만, **실전에서 터질 수 있는 디테일**(relevance 임계값, 한글 인코딩, 타입 변환)을 놓치고 있었음
- 3개 AI 리뷰를 거쳐 **9점 수준**으로 보강됨
- 사장님이 외부 검토를 요청한 것은 **100% 옳은 판단**이었음

---

## 0. 3개 AI 피드백 종합 분석

### 만장일치 (3/3 동의 — 무조건 따름)

| # | 항목 | 합의 내용 |
|---|------|-----------|
| 1 | Step 2+3 통합 | 매칭 결과 표시 + 검증 투표는 같은 UI, 한번에 구현 |
| 2 | 온톨로지 화면 위치 | C안: HomeScreen 서브화면 (Navigator.push). 7번째 탭 절대 안됨 |
| 3 | embedding 제외 | /api/ontology/map에서 embedding 컬럼 반드시 제외 (1.4MB → ~50KB) |
| 4 | category 컬럼 추가 | ontology_nodes에 category TEXT 컬럼 + 인덱스 필요 |
| 5 | 기존 4건 재매칭 | /api/ontology/retry-pending 실행하여 빈 상태 방지 |
| 6 | MVP 먼저 | Step 1+2+3 완성 → Phase 4 MVP 선언 → 나머지는 후속 |

### 다수결 (2/3 동의 — 채택하되 소수 의견 반영)

| # | 항목 | 다수 의견 | 소수 의견 | 최종 결정 |
|---|------|-----------|-----------|-----------|
| 1 | 상태 관리 | Provider 최소 도입 (Grok, Sonnet) | setState 유지 (Gemini) | **Provider 채택** — 이미 dependency에 있고, 228개 노드 3번 호출 방지 |
| 2 | 투표 인증 | SharedPreferences 제한 (Sonnet, Gemini) | 백엔드 RLS (Grok) | **SP 채택 (MVP)** — 로그인 기능 추가 시 백엔드로 전환 |
| 3 | 탐색 UI | 카드 그리드 + 카테고리 필터 + 검색 (Grok, Gemini) | 3단계 drill-down (Sonnet) | **카드 그리드 채택** — 카테고리 칩 + 검색바 + 2열 그리드 |

### 의견 분산 (각각 다름 — 총책임자 판단)

| # | 항목 | Grok | Sonnet | Gemini | 최종 결정 |
|---|------|------|--------|--------|-----------|
| 1 | 폴링 전략 | B안: 2초×5회 폴링 | A안: 5초 후 1회 | 하이브리드: 3초×3회 | **B안 채택 (2초×5회)** — 아래 근거 참조 |
| 2 | 결과 UX | BottomSheet 유지 | SnackBar + 액션버튼 | 상세 화면 이동 + 스켈레톤 | **SnackBar 액션 → BottomSheet** — 아래 근거 참조 |
| 3 | Step 4 순서 | Step 2→3→4 | Step 2+3→4 | Step 4→2+3 | **Step 2+3 먼저** — 아래 근거 참조 |

### 최종 결정 근거

**폴링 전략 — B안 (2초×5회) 채택 이유:**
- A안(5초 후 1회)은 매칭이 3초에 끝나도 5초를 기다려야 함 → 불필요한 지연
- B안은 매칭 완료 즉시 결과를 보여줄 수 있음 (3초면 2번째 폴링에서 잡힘)
- 5회 × 228개 노드 규모 → 서버 부하 무시 가능 수준
- 10초 후에도 pending이면 "목록에서 확인하세요" — Grok 제안 그대로

**결과 UX — SnackBar 액션 → BottomSheet 채택 이유:**
- Grok안(BottomSheet 즉시)은 다이얼로그 닫자마자 또 뜨는 느낌 → Sonnet 지적이 맞음
- Gemini안(화면 전환 + 스켈레톤)은 좋지만 별도 화면 구현 필요 → 공수 대비 효과 낮음
- Sonnet안(SnackBar 액션버튼)이 "강제하지 않되 접근 가능한" 가장 자연스러운 UX
- 사용자가 관심 있으면 버튼 눌러서 BottomSheet 확인, 없으면 무시

**Step 2+3 먼저 — Gemini 반대의견 기각 이유:**
- Gemini는 "탐색 화면 먼저 만들어야 매칭 결과 렌더링 방향이 보인다"고 주장
- 하지만 매칭 결과 UI는 탐색 화면과 독립적 (BottomSheet에 노드 이름+relevance만 표시)
- "제보 → AI 결과 확인"이 사용자에게 가장 먼저 전달되어야 할 핵심 가치 (Grok, Sonnet 동의)
- Step 4는 데이터가 쌓인 후에 더 의미 있음

---

## 1. 사전 작업 (백엔드 수정 — Phase 4 구현 전 반드시)

### 1-1. /api/ontology/map embedding 제외 (5분)

**파일**: `main.py` — `get_ontology_map()` 함수

```python
# 변경 전
nodes = supabase_admin.table("ontology_nodes").select("*").execute()

# 변경 후
nodes = supabase_admin.table("ontology_nodes").select(
    "id, type, name, description, data, country, source_url, created_at"
).execute()
```

**효과**: 응답 크기 ~1.4MB → ~50KB (97% 감소)
**합의**: 3/3 만장일치

### 1-2. ontology_nodes에 category 컬럼 추가 (10분)

**파일**: 새 마이그레이션 `migrations/013_ontology_category.sql`

```sql
-- ontology_nodes에 category 컬럼 추가
ALTER TABLE ontology_nodes ADD COLUMN IF NOT EXISTS category TEXT;

-- data JSONB에서 category 추출하여 채우기
UPDATE ontology_nodes SET category = data->>'category'
WHERE data->>'category' IS NOT NULL;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_ontology_nodes_category ON ontology_nodes(category);
```

**확인 필요**: data JSONB 안에 category 키가 있는지 실제 DB 조회로 확인
**합의**: 3/3 만장일치

### 1-3. 기존 제보 재매칭 (2분)

```bash
# 관리자 API 호출
curl -X POST "https://minjuai-production.up.railway.app/api/ontology/retry-pending" \
  -H "X-Admin-Key: ${ADMIN_SECRET_KEY}"
```

**목적**: 기존 unmatched 4건을 228개 노드 기준으로 재매칭
**합의**: 3/3 만장일치

---

## 2. Phase 4 MVP (Step 1 + 2 + 3)

### Step 1. API 연결 계층 (30분)

**파일**: `lib/services/api_service.dart`

추가할 메서드 6개:

```dart
// 온톨로지 전용 타임아웃 (Sonnet 제안 반영)
static const Duration _ontologyTimeout = Duration(seconds: 30);

// 1. 전체 온톨로지 그래프 (embedding 제외됨)
static Future<Map<String, dynamic>> getOntologyMap() async { ... }

// 2. 온톨로지 검색 (한글 인코딩 주의! — Sonnet 지적)
static Future<Map<String, dynamic>> searchOntologyNodes(String query) async {
  final encoded = Uri.encodeComponent(query);  // 필수!
  ...
}

// 3. 제보의 AI 매칭 결과 조회
static Future<Map<String, dynamic>> getReportOntology(String reportId) async { ... }

// 4. 시민 검증 투표
static Future<Map<String, dynamic>> verifyMatch(
  String reportId, String nodeId, bool isCorrect
) async { ... }

// 5. 노드별 연결 제보 목록
static Future<Map<String, dynamic>> getNodeReports(String nodeId) async { ... }

// 6. 온톨로지 통계
static Future<Map<String, dynamic>> getOntologyStats() async { ... }
```

**코딩 시 주의사항 (3개 AI 종합)**:
- `Uri.encodeComponent()` 한글 검색어 인코딩 필수 (Sonnet)
- `(json['relevance'] as num).toDouble()` 안전한 타입 변환 (Gemini)
- JSON 키값 백엔드와 정확히 일치하는지 크로스 체크 (Gemini)
- 온톨로지 API는 `_ontologyTimeout` (30초) 사용 (Sonnet)

### Step 1.5. OntologyProvider (20분)

**파일**: 새 파일 `lib/providers/ontology_provider.dart`

```dart
class OntologyProvider extends ChangeNotifier {
  List<dynamic> nodes = [];
  Map<String, dynamic> stats = {};
  bool isLoading = false;
  String? errorMessage;

  // 캐시: 이미 로딩됐으면 스킵
  Future<void> loadIfEmpty() async {
    if (nodes.isNotEmpty) return;
    isLoading = true;
    notifyListeners();

    final data = await ApiService.getOntologyMap();
    nodes = data['nodes'] ?? [];
    stats = await ApiService.getOntologyStats();

    isLoading = false;
    notifyListeners();
  }

  // 카테고리별 필터
  List<dynamic> getNodesByCategory(String category) {
    return nodes.where((n) => n['category'] == category).toList();
  }
}
```

**main.dart에 Provider 등록**:
```dart
ChangeNotifierProvider(create: (_) => OntologyProvider()),
```

**합의**: 2/3 (Grok, Sonnet 동의 / Gemini는 setState 선호하나 Provider가 더 효율적)

### Step 2+3. 제보 후 AI 매칭 결과 + 시민 검증 (2시간)

**파일**: `lib/screens/monitoring_screen.dart`

#### 변경할 흐름:

```
[현재]
제보 등록 → Navigator.pop → SnackBar "제보가 등록되었습니다!" → 끝

[변경 후]
제보 등록 → Navigator.pop → SnackBar "제보 등록 완료! [AI 분석 결과 보기]"
                                         ↓ (사용자가 버튼 터치)
                              BottomSheet (폴링 + 결과 표시 + 검증 버튼)
```

#### BottomSheet 상세 흐름:

```
[BottomSheet 열림]
┌──────────────────────────────────┐
│ 🤖 AI 분석 중...                │
│ ████████░░ (프로그레스 바)       │
│                                  │
│ 제보: "도로 파손 심각"           │
│ 분석 소요: 약 5초               │
└──────────────────────────────────┘
          ↓ (2초 간격 폴링, 최대 5회)
┌──────────────────────────────────┐
│ ✅ AI 분석 완료!                 │
│                                  │
│ 🏷️ 도로·교통 인프라   85% 일치  │ ← 0.6 이상: 강조 (파란색)
│ 🏷️ 지역 안전 문제     42% 일치  │ ← 0.4~0.6: 연하게 (회색)
│                                  │
│ 이 분석이 맞나요?                │
│ [맞아요 👍]    [아니에요 👎]     │
│                                  │
│ ⭐ 검증 참여 +3P                 │
└──────────────────────────────────┘
          ↓ (10초 후에도 pending인 경우)
┌──────────────────────────────────┐
│ ⏳ 분석이 조금 오래 걸리고 있어요│
│                                  │
│ 제보 목록에서 나중에 확인하세요  │
│ [확인]                           │
└──────────────────────────────────┘
```

#### Relevance 임계값 정책 (Sonnet 제안 — Critical):

```dart
// 현재 DB 데이터가 0.32~0.40 수준 → 현실적 기준 설정
Widget _buildRelevanceBadge(double relevance) {
  if (relevance >= 0.6) {
    // 강한 매칭: 파란색 강조, "AI 연결 확인"
    return _highMatchBadge(relevance);
  } else if (relevance >= 0.35) {
    // 참고 수준: 연한 회색, "참고 연결"
    return _mediumMatchBadge(relevance);
  } else {
    // 0.35 미만: 숨기기 (사용자에게 노출하지 않음)
    return SizedBox.shrink();
  }
}
```

**주의**: Sonnet이 발견한 Critical 이슈 — 현재 relevance가 0.32~0.40으로 전반적으로 낮음.
0.5 기준을 쓰면 대부분 숨겨짐. **0.35를 최소 임계값으로 설정** (현실적 조정).
배포 후 데이터가 쌓이면 임계값 상향 조정.

#### 시민 검증 중복 투표 방지:

```dart
// SharedPreferences 기반 (MVP 단계)
Future<bool> hasAlreadyVerified(String reportId, String nodeId) async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getBool('verified_${reportId}_${nodeId}') ?? false;
}

Future<void> markAsVerified(String reportId, String nodeId) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setBool('verified_${reportId}_${nodeId}', true);
}
```

#### 제보 목록에서 온톨로지 상태 표시:

기존 제보 목록 카드에 상태 뱃지 추가:
- `pending` → "🔄 분석 중"
- `matched` → "✅ AI 분석 완료" (터치하면 결과 BottomSheet)
- `unmatched` → "📝 새로운 이슈" (기존 온톨로지에 없는 주제)
- `filtered` → 표시 안 함

---

## 3. Phase 4 확장 (MVP 이후)

### Step 4. 온톨로지 탐색 화면 (2시간)

**파일**: 새 파일 `lib/screens/ontology_explore_screen.dart`

#### UI 구조:

```
┌──────────────────────────────────┐
│ ← 민주AI 정책 지식맵            │
├──────────────────────────────────┤
│ 🔍 검색: _________________      │
├──────────────────────────────────┤
│ [전체][사회][경제][환경]         │
│ [생활][미래][정치]               │ ← 카테고리 Chip (가로 스크롤)
├──────────────────────────────────┤
│ ┌────────┐ ┌────────┐           │
│ │🏥 복지 │ │🏫 교육 │           │ ← 2열 GridView
│ │ 23건   │ │ 18건   │           │
│ └────────┘ └────────┘           │
│ ┌────────┐ ┌────────┐           │
│ │🚗 교통 │ │💰 경제 │           │
│ │ 15건   │ │ 31건   │           │
│ └────────┘ └────────┘           │
└──────────────────────────────────┘
          ↓ (카드 터치)
┌──────────────────────────────────┐
│ ← 교육 관련 이슈                │
├──────────────────────────────────┤
│ 📌 무상급식 확대                 │
│ 시민 제보 8건 | AI 매칭 91%     │
│ "학교 급식 질 개선 요구..."      │
├──────────────────────────────────┤
│ 📌 학교 폭력 대책                │
│ 시민 제보 7건 | AI 매칭 87%     │
└──────────────────────────────────┘
```

**진입점**: HomeScreen에 "정책 지식맵 탐색하기" 카드 추가
**합의**: 3/3 (HomeScreen 서브화면)

#### 텍스트 오버플로우 대응 (Gemini 지적):

```dart
Text(
  node['description'] ?? '',
  maxLines: 2,
  overflow: TextOverflow.ellipsis,  // 필수!
)
```

### Step 5. 홈 대시보드 강화 (1시간)

**파일**: `lib/screens/home_screen.dart`

기존 `ontology_coverage` % 하나 → 상세 통계 카드:

```
┌──────────────────────────────────┐
│ 🧠 AI 이슈 분석 현황            │
│                                  │
│ 총 제보: 156건                   │
│ AI 분석 완료: 128건 (82%)        │
│ ████████████████░░░░ 82%         │
│                                  │
│ 시민 검증: 45건 (정확도 91%)     │
│ 이번 주 핫이슈: 전세 사기 🔥     │
│                                  │
│ [정책 지식맵 탐색하기 →]         │ ← Step 4 진입점
└──────────────────────────────────┘
```

---

## 4. 백엔드 추가 수정 사항

### 4-1. /api/ontology/map 카테고리별 통계 추가

```python
# 노드별 연결 제보 수 포함
nodes = supabase_admin.table("ontology_nodes").select(
    "id, type, name, description, category, data, country, source_url, created_at"
).execute()
```

### 4-2. 제보 목록 API에 ontology_status 포함 확인

현재 `/api/districts/{district}/reports` 응답에 `ontology_status`가 포함되는지 확인.
없으면 추가 필요 (제보 목록에서 상태 뱃지 표시용).

---

## 5. 코딩 시 필수 체크리스트 (3개 AI 종합)

### 반드시 지키기 (Critical)

- [ ] `/api/ontology/map`에서 embedding 컬럼 제외 후 Flutter 작업 시작
- [ ] `Uri.encodeComponent()` 한글 검색어 인코딩 (Sonnet)
- [ ] `(json['relevance'] as num).toDouble()` 안전한 타입 변환 (Gemini)
- [ ] 텍스트 위젯에 `TextOverflow.ellipsis` + `maxLines` 적용 (Gemini)
- [ ] relevance 0.35 미만은 UI에서 숨기기 (Sonnet — 현재 데이터 기준 조정)
- [ ] 온톨로지 API 타임아웃 30초로 분리 (Sonnet)

### 하면 좋지만 MVP 이후 (Nice to have)

- [ ] ApiService → Dio + Interceptor 전환 (Grok 추천, 하지만 현재 http로 충분)
- [ ] OntologyNode, ReportMatch 등 모델 클래스 (Grok 추천)
- [ ] 오프라인 제보 큐 (Sonnet 추천 — 지하철 등 불안정 환경)
- [ ] Supabase RLS 정책 재확인 (Grok)

---

## 6. 일정 계획

### Day 1 (오늘) — 백엔드 사전 작업 + Step 1

| 시간 | 작업 | 산출물 |
|------|------|--------|
| 30분 | 사전작업 1-1, 1-2, 1-3 (embedding 제외, category 추가, 재매칭) | 백엔드 준비 완료 |
| 30분 | Step 1: api_service.dart 메서드 6개 추가 | API 연결 완료 |
| 20분 | Step 1.5: OntologyProvider 생성 + main.dart 등록 | 상태 관리 준비 |

### Day 1~2 — Step 2+3 (MVP 핵심)

| 시간 | 작업 | 산출물 |
|------|------|--------|
| 1시간 | 제보 등록 후 SnackBar 액션 + BottomSheet 폴링 | AI 결과 표시 |
| 30분 | 시민 검증 버튼 + SharedPreferences 중복 방지 | 검증 투표 |
| 30분 | 제보 목록 카드에 ontology_status 뱃지 | 상태 시각화 |
| 30분 | 테스트 + 디버깅 + Railway 배포 | **MVP 완성** |

### Day 2~3 — Step 4 + 5 (확장)

| 시간 | 작업 | 산출물 |
|------|------|--------|
| 2시간 | 온톨로지 탐색 화면 (카드 그리드 + 검색 + 카테고리) | 지식맵 탐색 |
| 1시간 | 홈 대시보드 통계 카드 + 탐색 진입점 | 대시보드 강화 |

---

## 7. 성공 기준

| 항목 | 기준 |
|------|------|
| MVP 완성 | 제보 → AI 매칭 결과 BottomSheet → 검증 투표 → 정상 동작 |
| 성능 | /api/ontology/map 응답 < 100KB, 로딩 < 2초 |
| UX | 폴링 10초 이내 결과 표시 또는 "나중에 확인" 안내 |
| 안정성 | 네트워크 오류 시 앱 크래시 없음, 빈 상태 처리 완료 |
| 데이터 | 기존 4건 재매칭 완료, 최소 1건 이상 matched 상태 확인 |

---

## 8. 리스크 관리

| 리스크 | 발생 시 대응 |
|--------|-------------|
| ontology_nodes.data에 category 키가 없음 | policy_topics.category_group 기반으로 수동 매핑 |
| relevance가 전부 0.4 미만 | 임계값을 0.3으로 낮추고 "참고 수준" 레이블로 표시 |
| Railway 배포 후 타임아웃 | ontology API 타임아웃 30초로 이미 분리 |
| 한글 검색 400 에러 | Uri.encodeComponent() 적용 확인 |
| JSON 타입 불일치 크래시 | (json['x'] as num).toDouble() 패턴 적용 |

---

**이 계획서는 3개 AI의 크로스 리뷰를 거친 검증된 계획입니다.**
**사장님 확인 후 실행에 들어갑니다.**
