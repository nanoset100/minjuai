# 정책AI MVP — Product Requirements Document
> 작성: 2026-04-08  
> 대상: Claude Code (개발 AI 에이전트)  
> 스택: FastAPI + Supabase + Railway + GPT-4o mini  
> 저장소: github.com/nanoset100/minjuai

---

## 한 줄 제품 정의

> **"내 지역구 의원이 이 정책에 뭐라 했는지 보고, 마음에 안 들면 바로 편지를 보내는 앱"**

---

## 왜 이 두 기능인가 — 기획 의도

지금까지 국내 정치 정보 앱은 전부 **"보는 앱"** 이었다.  
정치랭크, 열려라 국회, 공식 국회 앱 — 모두 정보를 나열하고 끝낸다.  
시민이 할 수 있는 행동이 없다.

정책AI MVP는 다르다.

```
정책 이슈 확인 (기능 A)  →  마음에 안 들면 편지 (기능 B)
```

**정보를 보고 행동까지 이어지는 완결 구조**가 국내 최초다.  
영국 TheyWorkForYou는 이 구조로 연간 18만 건의 시민 편지를 만들어냈다.

---

## 핵심 사용자 시나리오 (User Story)

### 시나리오 1 — 정책 반응 탐색
```
박지수(25세, 광주 북구)는 뉴스에서 최저임금 법안을 봤다.
"우리 동네 의원은 이걸 어떻게 생각하나?" 궁금하다.
앱을 열고 주소를 입력한다.
→ 내 의원이 이 법안에 "찬성 발언 있음"이라고 나온다.
→ "잘했네" 하고 앱을 닫는다.
```

### 시나리오 2 — 편지 발송
```
김민준(32세, 광주 서구)은 같은 뉴스를 보고 화가 났다.
우리 의원이 침묵하고 있다는 걸 확인했다.
"한마디 해야겠다" → 편지 작성 버튼을 탭한다.
3줄을 쓰고 발송한다.
"광주 서구 의원실에 전달됐습니다" 화면을 본다.
→ 친구에게 스크린샷을 보낸다. "나 진짜로 의원한테 편지 보냄"
```

시나리오 2가 이 앱의 성장 엔진이다. **"실제로 보냈다"는 경험은 공유된다.**

---

## 기능 명세

---

### 기능 A. 정책 이슈별 의원 반응 시각화

#### A-1. 진입 화면 — 내 의원 찾기

**URL:** `/`

**화면 요소:**
- 헤드카피: "우리 지역구 의원, 지금 뭐 하고 있나요?"
- 주소 입력창 (시·구·동 3단계 선택 또는 자유 입력)
- 입력 즉시 → 해당 지역구 의원 카드 표시

**의원 카드 구성:**
```
[사진]  홍길동 의원
        광주 북구 갑 | 더불어민주당
        환경노동위원회 소속
        [이번 주 활동 보기 →]
```

**기술 구현:**
```python
# GET /api/member/by-address?district=광주+북구
# 300개 지역구 매핑 DB (기존 보유) → 의원 정보 반환
```

---

#### A-2. 정책 이슈별 반응 화면

**URL:** `/issues` 또는 의원 카드 클릭 후

**화면 구성:**

```
[오늘의 정책 이슈]  ← 이슈맨 AI가 매일 자동 수집

┌─────────────────────────────────────┐
│  최저임금 1만 2천원 법안              │
│  2026-04-07 | 환경노동위원회 관련     │
│                                     │
│  홍길동 의원 반응                    │
│  ● 찬성 발언  "노동자 생활 안정..."   │
│  [발언 전문 보기]  [편지 보내기 →]   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  청년 주거 지원 확대 법안             │
│  2026-04-06 | 국토교통위원회 관련     │
│                                     │
│  홍길동 의원 반응                    │
│  ○ 침묵  (관련 발언 없음)            │
│  [이 이슈로 편지 쓰기 →]            │
└─────────────────────────────────────┘
```

**반응 분류 3종:**
- `● 찬성/지지` — 관련 발언 확인됨, 긍정적 내용
- `● 반대/우려` — 관련 발언 확인됨, 부정적 내용
- `○ 침묵` — Assembly API 기준 관련 발언 없음

> ⚠️ "침묵"은 "데이터 없음"과 다르다. UI에서 명확히 구분 필수.
> "데이터 수집 중"은 별도 상태로 표시.

**백엔드 파이프라인:**

```python
# 매일 새벽 2시 Railway Cron 실행

# 1단계: 이슈맨 뉴스 수집 (기존 agents/ 활용)
issues = issuernan_agent.fetch_today()  # 이미 구현됨

# 2단계: 위원회 키워드 매핑
for issue in issues:
    committee = keyword_mapper.match(issue.title)
    # 예: "최저임금" → 환경노동위원회

# 3단계: 해당 위원회 소속 의원 발언 조회
for member in committee.members:
    speeches = assembly_api.get_speeches(
        member_id=member.id,
        keywords=issue.keywords,
        days=30
    )

# 4단계: GPT-4o mini로 찬반 분류 + 요약
stance = gpt_client.classify_stance(
    issue=issue.title,
    speeches=speeches,
    prompt=STANCE_CLASSIFICATION_PROMPT  # 아래 별도 정의
)

# 5단계: Supabase issue_reactions 테이블에 저장
# 조회 시 DB 읽기만 → GPT 호출 0건
```

**GPT 프롬프트 설계 (STANCE_CLASSIFICATION_PROMPT):**

```
당신은 국회 발언 분석가입니다.

다음 정책 이슈에 대해 의원의 발언을 분석하여 입장을 분류하세요.

정책 이슈: {issue_title}
의원 발언 목록: {speeches}

분류 기준:
- "찬성": 이슈에 긍정적, 지지하는 발언이 명확히 있는 경우
- "반대": 이슈에 부정적, 반대하는 발언이 명확히 있는 경우  
- "침묵": 관련 발언이 없거나 중립적인 경우

반드시 JSON으로만 응답:
{
  "stance": "찬성|반대|침묵",
  "confidence": 0.0~1.0,
  "summary": "한 줄 요약 (30자 이내)",
  "evidence": "근거 발언 원문 50자 이내 (없으면 null)"
}

주의: 확실하지 않으면 "침묵"으로 분류. 과도한 추론 금지.
```

**Supabase 테이블 스키마:**

```sql
-- issue_reactions 테이블
CREATE TABLE issue_reactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_id UUID REFERENCES issues(id),
  member_id VARCHAR REFERENCES members(mona_cd),
  stance VARCHAR CHECK (stance IN ('찬성', '반대', '침묵', '수집중')),
  confidence FLOAT,
  summary TEXT,
  evidence TEXT,
  data_date DATE NOT NULL,
  generated_at TIMESTAMPTZ DEFAULT now()
);

-- issues 테이블
CREATE TABLE issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR NOT NULL,
  source_url TEXT,
  committee VARCHAR,
  keywords TEXT[],
  collected_at TIMESTAMPTZ DEFAULT now()
);
```

**API 엔드포인트:**

```python
# GET /api/issues?member_id={id}&limit=10
# 반환: 해당 의원의 최근 이슈별 반응 목록

# GET /api/issues/{issue_id}/reactions
# 반환: 특정 이슈에 대한 전체 의원 반응 (지역구별 필터 가능)
```

---

### 기능 B. 의원에게 편지 보내기

#### B-1. 편지 작성 화면

**URL:** `/letter/{member_id}` 또는 이슈 카드 → "편지 보내기" 버튼

**화면 구성:**

```
홍길동 의원에게 편지 쓰기
광주 북구 갑 | 환경노동위원회

[관련 이슈: 최저임금 1만 2천원 법안]  ← 이슈에서 진입 시 자동 연결

닉네임 (선택): [____________]
               실명 불필요, 의원실에는 "광주 시민"으로 전달

편지 내용:
┌────────────────────────────────────┐
│                                    │
│  최대 500자                        │
│                                    │
└────────────────────────────────────┘

[AI가 먼저 검토합니다 — 욕설·스팸 자동 필터]

              [취소]  [의원실에 전달하기 →]
```

**UX 원칙:**
- 실명 불필요 — 진입 장벽 최소화
- 로그인 불필요 — Phase 1에서는 완전 익명
- 글자수 500자 제한 — 짧고 명확한 편지 유도
- "AI 검토" 안내 — 스팸 방지 신뢰 형성

#### B-2. 발송 처리

**백엔드 처리 순서:**

```python
# POST /api/letters

async def send_letter(letter: LetterRequest):

    # 1단계: AI 스팸/욕설 필터
    filter_result = await gpt_client.filter_letter(
        content=letter.content,
        prompt=LETTER_FILTER_PROMPT
    )
    if filter_result.blocked:
        return {"status": "blocked", "reason": filter_result.reason}

    # 2단계: 의원실 이메일 주소 조회
    member = await db.get_member(letter.member_id)
    # 이메일: Assembly API ALLNAMEMBER 엔드포인트 공개 데이터

    # 3단계: 편지 DB 저장 (발송 전)
    letter_id = await db.save_letter({
        "member_id": letter.member_id,
        "content": letter.content,
        "issue_id": letter.issue_id,  # 이슈 연결 시
        "nickname": letter.nickname or "광주 시민",
        "status": "pending"
    })

    # 4단계: SendGrid로 발송
    result = await sendgrid.send(
        to=member.email,
        subject=f"[정책AI 시민편지] {member.name} 의원님께",
        body=build_letter_email(letter, member)
    )

    # 5단계: 발송 완료 업데이트
    await db.update_letter_status(letter_id, "sent")

    return {
        "status": "sent",
        "letter_id": letter_id,
        "member_name": member.name,
        "sent_at": datetime.now().isoformat()
    }
```

**이메일 템플릿 (build_letter_email):**

```
수신: {의원실 공식 이메일}
발신: noreply@jeongchaek.ai
제목: [정책AI 시민편지] {의원명} 의원님께

안녕하세요, {의원명} 의원님.

정책AI(jeongchaek.ai) 플랫폼을 통해 지역구 시민의 편지가 전달됩니다.

---
보낸 사람: {닉네임} (광주 {지역구} 지역 시민)
관련 정책: {이슈 제목 — 있는 경우}

{편지 내용}
---

이 편지는 정책AI 시민 참여 플랫폼(jeongchaek.ai)을 통해 발송되었습니다.
회신은 이 이메일로 보내주시면 시민에게 전달됩니다.
```

**필터 프롬프트 (LETTER_FILTER_PROMPT):**

```
다음 편지가 의원실 발송에 적합한지 판단하세요.

편지 내용: {content}

차단 기준 (하나라도 해당되면 blocked=true):
- 욕설, 비속어, 혐오 표현 포함
- 특정인에 대한 명백한 허위 사실
- 스팸성 반복 내용 또는 의미 없는 텍스트
- 100자 미만의 지나치게 짧은 내용

JSON으로만 응답:
{"blocked": true/false, "reason": "차단 이유 (blocked=true일 때만)"}
```

#### B-3. 발송 확인 화면 ("전달됨" 화면)

**이 화면이 이 앱의 가장 중요한 화면이다.**

```
┌─────────────────────────────────────┐
│                                     │
│   ✓  전달됐습니다                   │
│                                     │
│   홍길동 의원실에                   │
│   방금 편지가 전달됐어요             │
│                                     │
│   2026-04-08 오후 3:42              │
│   편지 번호 #00847                  │
│                                     │
│   ─────────────────────             │
│   지금까지 광주 시민                │
│   총 847건의 편지를 보냈어요         │
│   ─────────────────────             │
│                                     │
│   [이미지로 저장]  [링크 복사]      │
│                                     │
│   [다른 이슈 보기]                  │
│                                     │
└─────────────────────────────────────┘
```

**왜 이 화면이 핵심인가:**
- "총 847건" 누적 카운터 → 나도 이 운동의 일부라는 소속감
- 이미지 저장 → 인스타 스토리 공유 유도
- 링크 복사 → "나 편지 보냄" SNS 공유
- 편지 번호 → 실제로 기록됐다는 신뢰

---

## 기술 구현 상세

### 환경 변수 추가 필요

```env
# .env에 추가
SENDGRID_API_KEY=sg.xxxx
LETTER_FROM_EMAIL=noreply@jeongchaek.ai
LETTER_FROM_NAME=정책AI 시민편지
ASSEMBLY_MEMBER_EMAIL_CACHE=true  # 이메일 DB 로컬 캐싱
```

### 신규 파일 구조

```
minjuai/
├── services/
│   ├── assembly_mapper.py      # 기존 — 위원회 키워드 매핑
│   ├── scorecard_cache.py      # 기존
│   ├── reaction_pipeline.py    # 신규 — 이슈×반응 배치
│   └── letter_service.py       # 신규 — 편지 발송
├── agents/
│   └── issuernan_agent.py      # 기존 — 뉴스 수집
├── routers/
│   ├── issues.py               # 신규 — /api/issues
│   └── letters.py              # 신규 — /api/letters
└── mvp/
    └── index.html              # 신규 — MVP 프론트엔드 단일 파일
```

### Railway Cron 스케줄

```
# Procfile에 추가
worker: python -m services.reaction_pipeline

# railway.json cron 설정
{
  "crons": [
    {
      "path": "/cron/reaction-pipeline",
      "schedule": "0 2 * * *"    // 매일 새벽 2시
    },
    {
      "path": "/cron/scorecard",
      "schedule": "0 3 * * *"    // 매일 새벽 3시 (기존)
    }
  ]
}
```

### Assembly API Fallback (v1.1 정의 그대로)

| 단계 | 조건 | 동작 |
|------|------|------|
| 1순위 | API 정상 | DB 저장 후 제공 |
| 2순위 | API 다운 | 캐시 제공 + 날짜 명시 |
| 3순위 | 7일 초과 | "데이터 갱신 중" 표시 |

---

## MVP 프론트엔드 설계

### 단일 HTML 파일 원칙

```
mvp/index.html  — 모든 화면을 하나의 파일로 관리
                  JS로 화면 전환 (SPA 방식)
                  외부 프레임워크 없음 — Vanilla JS
```

### 화면 전환 흐름

```
[홈] 주소 입력
    ↓
[내 의원] 의원 카드 + 오늘의 이슈 목록
    ↓ 이슈 탭
[이슈 상세] 반응 상세 + 발언 원문
    ↓ 편지 버튼
[편지 작성] 닉네임 + 내용 입력
    ↓ 발송
[전달 확인] "전달됐습니다" + 누적 카운터 + 공유 버튼
```

### 모바일 퍼스트 CSS 기준

```css
/* 기준 해상도: 390px (iPhone 14) */
/* 최대 컨텐츠 폭: 480px */
/* 폰트: 시스템 폰트 (-apple-system, Pretendard, sans-serif) */
/* 주요 컬러: 
   - 메인: #1D9E75 (정책AI 그린 — 신뢰·성장)
   - 강조: #378ADD (정보·링크)
   - 위험: #E24B4A (반대 의견)
   - 배경: #F8F8F6
*/
```

### SEO 메타태그 (의원별 페이지)

```html
<title>홍길동 의원 정책 반응 | 정책AI</title>
<meta name="description" content="광주 북구 갑 홍길동 의원의 최근 정책 활동과 시민 편지를 확인하세요.">
<meta property="og:title" content="홍길동 의원에게 편지 보내기 | 정책AI">
<meta property="og:image" content="/og/member/홍길동.png">  ← 공유 시 의원 카드 이미지
```

---

## 출시 기준 (Definition of Done)

Phase 1 완료 조건 — 이걸 다 만족해야 Phase 2(홍보)를 시작한다:

```
기능 완성:
  ✓ 광주 8개 지역구 주소 → 의원 매핑 100% 작동
  ✓ 이슈맨 수집 이슈 → 의원 반응 매핑 최소 5건 이상
  ✓ 편지 작성 → SendGrid 발송 → "전달됨" 화면 완전 작동
  ✓ 스팸 필터 테스트 10건 이상 통과
  ✓ 모바일(390px) 레이아웃 깨지지 않음

데이터 품질:
  ✓ 의원 이메일 8개 전부 검증 완료 (실제 발송 테스트)
  ✓ AI 반응 분류 정확도 수동 검토 10건 이상
  ✓ "AI 생성 요약" 명시 + "오류 신고" 링크 모든 요약에 부착

신뢰 요소:
  ✓ data_date 모든 화면에 표시
  ✓ "전달됨" 확인 화면에 타임스탬프 + 편지 번호 표시
  ✓ 누적 편지 카운터 실시간 반영
```

---

## 하지 말아야 할 것 (Claude Code에게)

```
절대 금지:
  ✗ 성적표 기능 추가 — 이번 MVP에 없음
  ✗ 로그인/회원가입 구현 — 사용자 0명 단계에서 불필요
  ✗ 조회 시 GPT 호출 — 반드시 배치 캐시에서 읽기만
  ✗ 전국 의원 나열 화면 — 정치랭크와 같은 실수
  ✗ 화려한 애니메이션/차트 — 빠른 로딩이 우선
  ✗ 외부 CSS 프레임워크 — 파일 크기 최소화

우선순위 착각 금지:
  ✗ "의원에게 묻는다" 기능 — Phase 3에서 구현
  ✗ 푸시 알림 — 사용자 확보 후
  ✗ 다크모드 — MVP에서 불필요
  ✗ 앱스토어 배포 준비 — MAU 50명 이후
```

---

## 성공 지표

| 시점 | 지표 | 목표 |
|------|------|------|
| MVP 완성 (D+42) | 광주 8개 지역구 편지 발송 테스트 | 전원 성공 |
| Phase 2 시작 (D+50) | 실제 시민 편지 발송 수 | 10건 이상 |
| D+70 | 누적 편지 발송 | 50건 이상 |
| D+70 | 월 방문자 | 100명 이상 |
| D+90 | 의원실 응답 | 1건 이상 |

> 의원실 응답 1건 = 언론 보도 + 신뢰도 폭발. 이게 Phase 3의 불쏘시개다.

---

## 개발 우선순위 (Claude Code 실행 순서)

```
Week 1-2: 데이터 기반
  1. Assembly API 클라이언트 완성 + 광주 8개 의원 이메일 검증
  2. 위원회 키워드 매핑 딕셔너리 완성
  3. Supabase issues + issue_reactions + letters 테이블 생성

Week 3-4: 백엔드 완성
  4. reaction_pipeline.py — 이슈×반응 배치 파이프라인
  5. letter_service.py — SendGrid 연동 + 필터 + 발송
  6. /api/issues, /api/letters 엔드포인트

Week 5: 프론트엔드 + QA
  7. mvp/index.html — 5개 화면 완성
  8. 모바일 레이아웃 검증
  9. 편지 발송 end-to-end 테스트 (실제 발송 확인)
  10. AI 반응 분류 품질 검토 10건
```

---

## 참고 — 경쟁 서비스 교훈

| 서비스 | 실패 원인 | 정책AI가 피할 것 |
|--------|-----------|-----------------|
| 정치랭크 | 전국 나열, 행동 없음, 광고 | 지역 특화 + 편지 행동 + 광고 없음 |
| 국회 공식 앱 | UX 최악, 시민 참여 없음 | 모바일 퍼스트 + 편지 기능 |
| PUM 정치인 | 별점 평가 → 편향 논란 | AI 데이터 기반 + 오류 신고 투명성 |

---

## 롤모델 — TheyWorkForYou (영국)

- 2003년 자원봉사자 10명이 만들기 시작
- 우편번호 입력 → 내 의원 + 투표 기록 + 편지 발송
- 현재 월 15만 방문, 선거철 30만
- 연간 18만 건 편지 발송, 의원 응답률 59%

**정책AI가 만들려는 것이 바로 이것의 한국판이다.**

---

*PRD 버전: v1.0 | 작성: 2026-04-08 | 다음 검토: MVP 완성 시*
