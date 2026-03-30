# Phase 4: Flutter 앱 온톨로지 연동 — 전문가 리뷰 요청

## 나는 누구인가
"민주AI" (세계 최초 AI 운영 정당 앱)의 앱 총책임자입니다.
- FastAPI 백엔드 + Supabase PostgreSQL + pgvector
- Flutter 앱 (6탭 구조)
- Railway 배포 (https://minjuai-production.up.railway.app)
- AI: OpenAI GPT-4o mini + text-embedding-3-small

Phase 1~3 완료 (DB 마이그레이션 → 서버 구현 → 노드 확장 228건).
이제 Phase 4: Flutter 앱에서 온톨로지 시스템을 연동하려 합니다.

---

## 현재 시스템 구조

### 백엔드 온톨로지 API (이미 완성, Railway 운영 중)

| # | Method | Endpoint | 응답 형태 |
|---|--------|----------|-----------|
| 1 | GET | `/api/ontology/map` | `{ nodes: [...], edges: [...], total_nodes, total_edges }` |
| 2 | GET | `/api/ontology/search?q=교육` | `{ results: [...], total }` |
| 3 | GET | `/api/districts/report/{report_id}/ontology` | `{ report_id, ontology_status, linked_nodes: [{relevance, ontology_nodes: {id, type, name, description}}], total_links }` |
| 4 | GET | `/api/ontology/node/{node_id}/reports` | `{ node_id, related_reports: [{district_reports: {id, title, content, created_at}}], total_reports }` |
| 5 | POST | `/api/districts/report/{report_id}/verify-match?node_id=xx&is_correct=true` | `{ status: "verified"/"rejected", verify_upvotes/verify_downvotes }` |
| 6 | GET | `/api/ontology/stats` | `{ total_reports, matched, unmatched, pending, match_rate, avg_relevance, verification_rate, pending_candidates, total_nodes, total_edges }` |
| 7 | POST | `/api/ontology/retry-pending` | 관리자 전용 (ADMIN_SECRET_KEY 필요) |

### 매칭 파이프라인 (백그라운드 동작)
```
시민 제보 POST → 즉시 저장 (ontology_status='pending') → 즉시 응답
                  ↓ BackgroundTasks (비동기)
                  악성 필터링 → pgvector Top 10 → GPT-4o mini 최종 매칭
                  → matched/unmatched/filtered/error
```

### 제보 등록 API 응답 형태
```json
// POST /api/districts/report
// 응답:
{
  "status": "success",
  "message": "제보가 등록되었습니다! (+10P)",
  "report": {
    "id": "uuid-xxxx",       // ← 이 report_id로 온톨로지 결과 조회
    "district": "서울 영등포구을",
    "title": "...",
    "content": "...",
    "ontology_status": "pending"
  },
  "points_earned": 10,
  "ontology_status": "pending"
}
```

### Flutter 앱 현재 상태

**구조:**
```
lib/
├── main.dart            (6탭 BottomNavigationBar + IndexedStack)
├── theme.dart           (AppTheme: primary #667EEA, secondary #764BA2)
├── screens/
│   ├── home_screen.dart       (대시보드, ontology_coverage % 표시만 있음)
│   ├── monitoring_screen.dart (의원감시 + 시민제보 — TabBarView 3탭)
│   ├── policies_screen.dart   (정책 연구)
│   ├── chat_screen.dart       (AI 챗봇)
│   ├── agents_screen.dart     (AI 에이전트 대시보드)
│   └── profile_screen.dart    (프로필/리더보드)
├── services/
│   └── api_service.dart       (모든 HTTP 호출, static 메서드)
└── models/
    ├── policy.dart
    └── chat_message.dart
```

**api_service.dart 패턴:**
```dart
class ApiService {
  static const String baseUrl = 'https://minjuai-production.up.railway.app';
  static const Duration _timeout = Duration(seconds: 10);

  // 모든 메서드가 static, try-catch로 감싸고, 실패시 빈 Map/List 반환
  static Future<Map<String, dynamic>> getXxx() async {
    try {
      final r = await http.get(Uri.parse('$baseUrl/api/xxx')).timeout(_timeout);
      if (r.statusCode == 200) return jsonDecode(r.body);
      return {};
    } catch (e) { return {}; }
  }
}
```

**현재 제보 제출 흐름 (monitoring_screen.dart):**
1. `_showReportDialogFor()` → AlertDialog로 입력
2. 유저가 "제보 등록" 누르면 → `Navigator.pop(context)` (다이얼로그 닫음)
3. `ApiService.submitDistrictReport()` 호출
4. 성공 시 SnackBar "제보가 등록되었습니다!" — **여기서 끝. AI 분석 결과 없음**

**온톨로지 관련 Flutter 코드: 없음** (api_service.dart에 온톨로지 메서드 0개)

**의존성:** http, shared_preferences, share_plus, flutter_dotenv, provider (있지만 미사용)

### DB 현재 데이터
- ontology_nodes: 228개 (6대 분류, 52개 주제)
- ontology_edges: 29개
- report_node_links: 0건 (아직 매칭된 제보 없음)
- district_reports: 4건 (전부 unmatched — 복지 관련 노드만 있을 때 등록된 것)
- node_candidates: 4개

---

## 내가 제안하는 구현 순서와 이유

### Step 1. API 연결 계층 (api_service.dart에 메서드 추가)
모든 UI가 의존하는 기반. 6개 메서드 추가:
- getOntologyMap(), searchOntologyNodes(q), getReportOntology(reportId)
- verifyMatch(reportId, nodeId, isCorrect), getNodeReports(nodeId), getOntologyStats()

### Step 2. 제보 후 AI 매칭 결과 표시 (핵심 가치)
현재 "제보 등록 완료" SnackBar → AI 분석 결과 다이얼로그로 변경.
제보 후 report_id를 받아서 → 폴링 또는 딜레이 후 `/api/districts/report/{id}/ontology` 조회
→ 매칭된 노드 이름 + relevance 표시.

### Step 3. 시민 검증 투표
Step 2에서 보여주는 매칭 결과에 "맞아요 / 아니에요" 버튼.
→ `/api/districts/report/{id}/verify-match` 호출.

### Step 4. 온톨로지 탐색 화면
228개 노드를 카테고리별로 탐색 + 검색.
노드 선택 → 연결된 제보 목록 표시.

### Step 5. 홈 대시보드 강화
기존 ontology_coverage만 있는 것 → 상세 통계 카드로 교체.

---

## 확인받고 싶은 질문들

### 아키텍처 질문

1. **폴링 vs 웹소켓**: 제보 후 AI 매칭 결과가 백그라운드에서 처리됨 (보통 3~10초). Flutter에서 결과를 어떻게 가져올 것인가?
   - A안: 제보 후 3초 대기 → 1회 조회 → 결과 없으면 "분석 중" 표시 + 목록에서 나중에 확인
   - B안: 2초 간격 폴링 (최대 5회, 10초) → 결과 나오면 즉시 표시
   - C안: 제보 목록에서 pending 상태인 것만 자동 새로고침
   - 어떤 방식이 UX와 서버 부하 면에서 최선인가?

2. **새 화면 vs 기존 화면 확장**: 온톨로지 탐색을 어디에 넣을 것인가?
   - A안: MonitoringScreen의 4번째 탭으로 추가 (현재 3탭)
   - B안: 별도 7번째 Bottom Tab
   - C안: HomeScreen에서 접근하는 서브 화면 (Navigator.push)
   - 6탭은 이미 많은 편. 어떻게 정리하는 것이 UX상 최선인가?

3. **상태 관리**: 현재 앱은 StatefulWidget + setState()만 사용, Provider는 의존성에 있지만 미사용. 온톨로지 데이터는 여러 화면에서 공유될 수 있음 (홈 통계, 제보 결과, 탐색 화면).
   - A안: 기존 패턴 유지 (각 화면에서 독립 호출)
   - B안: Provider로 온톨로지 상태 공유
   - 현재 앱 규모에서 어떤 것이 적절한가?

### UX 질문

4. **매칭 결과 표시 타이밍**: 다이얼로그를 닫은 후 SnackBar로 간단히 보여줄 것인가, 아니면 새로운 결과 화면(BottomSheet 등)으로 전환할 것인가? 고려사항: 매칭이 3~10초 걸리므로 사용자가 기다리는 동안의 경험.

5. **빈 상태 처리**: 현재 report_node_links가 0건이고 기존 4건 제보는 전부 unmatched. Phase 4 배포 직후에는 "분석 결과 없음"만 보일 텐데, 이때 사용자 경험을 어떻게 처리할 것인가? (기존 4건 재매칭? 테스트 데이터?)

6. **온톨로지 탐색 화면의 정보 밀도**: 228개 노드를 어떤 방식으로 보여줄 것인가?
   - A안: 6대분류 → 52주제 → 개별 노드 (3단계 drill-down)
   - B안: 검색 중심 + 인기 노드 상위 표시
   - C안: 카드 그리드 (카테고리 필터 + 검색)

### 기술 리스크 질문

7. **ontology_nodes에 category 컬럼이 있는가?** 228개 노드를 분류별로 그룹핑하려면 필요. Phase 3에서 추가했는지 확인 필요.

8. **verify-match API의 인증**: 현재 verify-match에는 인증이 없음 (누구나 호출 가능). 한 사람이 무한 투표하는 것을 어떻게 방지할 것인가? 백엔드 수정이 필요한가, Flutter 단에서 SharedPreferences로 제한할 것인가?

9. **대량 노드 로딩**: `/api/ontology/map`이 228개 노드 전체를 반환함 (embedding 포함 시 각 1536차원 float). 응답 크기가 클 수 있는데, embedding을 제외하고 반환하도록 백엔드를 수정해야 하는가?

---

## 요청사항

위 구현 순서(Step 1~5)와 9개 질문에 대해:

1. **구현 순서에 동의하는가?** 순서를 바꿔야 한다면 이유와 함께 제안해주세요.
2. **각 질문에 대한 구체적인 추천**과 근거를 제시해주세요.
3. **내가 놓치고 있는 리스크나 고려사항**이 있다면 지적해주세요.
4. **Flutter-FastAPI 연동에서 흔히 발생하는 실수**가 있다면 미리 알려주세요.

솔직하고 구체적인 피드백을 부탁드립니다. 과장이나 빈말은 필요 없습니다.
