# 외부 리뷰 반영 실행계획

**작성일**: 2026-04-01
**기반**: Claude Sonnet 리뷰 + 독립 진단서 종합
**원칙**: 기능 개발을 멈추지 않으면서, 긴급 수정만 먼저 처리

---

## Phase A: 긴급 수정 (오늘, 총 ~3시간)

기능 개발이 아니라 "버그 수정" 레벨. 지금 안 하면 나중에 더 큰 문제.

### A-1. APP_SECRET 인증 추가 (~1시간)
```
- Railway 환경변수에 APP_SECRET_KEY 추가
- dependencies.py에 verify_app_request 미들웨어 추가
- 쓰기 API(제보, 투표, 이슈 선택, 평가)에 적용
- 읽기 API(히트맵, 통계, 목록)는 열어둠
- Flutter 앱에 X-App-Key 헤더 추가 (다음 앱 작업 시)
```

### A-2. N+1 쿼리 수정 (~30분)
```
- get_report_ontology의 for문 개별 쿼리 → IN 쿼리 1번으로
- 대상: main.py 1372~1378 라인
```

### A-3. 히트맵 API limit 추가 (~30분)
```
- GET /api/heatmap/issues: report_node_links에 .limit(1000) 추가
- ilike 와일드카드 방어: region 파라미터에서 % _ 문자 제거
```

### A-4. BackgroundTasks 유실 방어 (~1시간)
```
- 매칭 시작 시 ontology_status = 'processing'으로 업데이트
- startup 이벤트에서 processing 상태 제보 자동 재매칭
- retry-pending과 유사하지만 자동 실행
```

---

## Phase B: Strategy Phase 4 개발 계속 (이번 주)

긴급 수정 후 바로 기능 개발 복귀.

### B-1. 새 이슈 제안 기능 (Strategy Phase 4)
```
- 시민이 258개 노드 외에 새 이슈를 직접 제안
- node_candidates 테이블 활용 (이미 존재)
- 백엔드 API + Flutter UI
```

---

## Phase C: 중기 개선 (Phase 4 완료 후)

### C-1. AI 매칭 정확도 개선
```
- ontology_nodes에 keywords TEXT[] 컬럼 추가 (마이그레이션)
- 258개 노드에 키워드 5~10개씩 추가
- 임베딩 재생성: name + description + keywords 합쳐서
- 정확도 재측정 (37% → 목표 60%+)
```

### C-2. Supabase RPC 히트맵 전환 (제보 500건 이상 시)
```
- PostgreSQL 함수로 GROUP BY 집계
- Python 인메모리 집계 제거
```

### C-3. citizen_selected few-shot 활용 (100건 이상 시)
```
- 시민 선택 데이터를 GPT 프롬프트 예시로 활용
- 매칭 정확도 추가 개선
```

---

## Phase D: 장기 (출시 전)

### D-1. Supabase Auth 도입
```
- 이메일/소셜 로그인
- JWT 검증 미들웨어
- RLS 정책 활성화
```

### D-2. main.py 자연스러운 분리
```
- 새 기능은 새 router 파일에 작성
- 기존 코드는 건드리지 않음
- 시간이 될 때 하나씩 이동
```

### D-3. 테스트 코드 (출시 직전)
```
- 핵심 API 5~10개만 통합 테스트
- 제보 등록 → 매칭 → 이슈 선택 → 히트맵 흐름
```

---

## 하지 않을 것

| 제안 | 이유 |
|------|------|
| main.py 전면 분리 | 1인 개발에서 대규모 리팩토링은 새 버그 유발 |
| fine-tuning | 데이터 부족 + 비용 대비 효과 불투명 |
| Redis 캐시 | 현재 규모에서 조기 최적화 |
| CORS 도메인 제한 | Flutter 앱이 네이티브라 CORS 무관, 웹 출시 시 적용 |

---

## 실행 순서 요약

```
오늘: A-1 → A-2 → A-3 → A-4 (긴급 수정 4건)
이번 주: B-1 (Strategy Phase 4)
다음 주~: C-1 (AI 정확도 개선)
출시 전: D-1, D-2, D-3
```

---

*두 AI 리뷰의 공통 의견은 전부 수용.*
*의견 차이는 "1인 개발 현실"에 맞는 쪽으로 결정.*
*기능 개발을 멈추지 않는 것이 최우선 원칙.*
