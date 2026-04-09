# 정책AI — CLAUDE.md
> Claude Code가 모든 세션 시작 시 반드시 읽는 파일입니다.
> 수정일: 2026-04-08

---

## 이 프로젝트가 무엇인가

**정책AI**는 시민이 자기 지역구 의원의 정책 반응을 확인하고,
마음에 안 들면 바로 편지를 보낼 수 있는 정치 참여 앱이다.

```
정책 이슈 확인 → 우리 의원 반응 보기 → 편지 발송
```

국내에 이 구조를 가진 서비스는 없다. 영국 TheyWorkForYou가 롤모델이다.

---

## 현재 스택

```
Backend:  FastAPI (Python) + Supabase (PostgreSQL) + Railway
Frontend: 단일 HTML 파일 (PWA, Vanilla JS)
AI:       OpenAI GPT-4o mini
Schedule: Railway Cron (매일 새벽 2시)
Repo:     github.com/nanoset100/minjuai
Live:     https://minjuai-production.up.railway.app
```

---

## MVP 확정 기능 — 딱 2개

### 기능 1. 정책 이슈별 의원 반응 시각화
- 이슈맨 AI가 수집한 뉴스 이슈 자동 분류
- 해당 이슈에 대한 의원 발언 → GPT가 찬성/반대/침묵 분류
- 매일 새벽 배치로 자동 업데이트 (조회 시 GPT 호출 절대 금지)

### 기능 2. 의원에게 편지 보내기
- 주소 입력 → 내 지역구 의원 자동 매핑
- 편지 작성 → AI 스팸 필터 → SendGrid 발송
- "전달됐습니다" 확인 화면 필수 (타임스탬프 + 편지 번호 + 누적 카운터)

---

## 절대 건드리지 말 것 (이번 MVP에서)

```
✗ 의원 성적표 기능        — Phase 3에서 구현
✗ 로그인 / 회원가입       — MAU 100명 이후
✗ 조회 시 GPT 호출        — 반드시 배치 캐시 읽기만
✗ 전국 의원 나열 화면     — 정치랭크와 같은 실수
✗ 인증 시스템             — 지금 불필요
✗ 앱스토어 배포 준비      — MAU 50명 이후
✗ 성인 광고 / 외부 광고   — 신뢰도 파괴
✗ 외부 CSS 프레임워크     — 파일 크기 최소화
```

---

## 데이터 파이프라인 원칙

```python
# 매일 새벽 2시 Railway Cron
1. 이슈맨 뉴스 수집 (agents/issuernan_agent.py — 기존)
2. 위원회 키워드 매핑 (services/assembly_mapper.py)
3. Assembly API 발언 조회 → GPT 찬반 분류
4. Supabase issue_reactions 테이블 저장

# 조회 시: DB 읽기만 → GPT 호출 0건
```

---

## Assembly API Fallback (필수 준수)

| 단계 | 조건 | 처리 |
|------|------|------|
| 1순위 | API 정상 | DB 저장 후 제공 |
| 2순위 | API 다운/누락 | 캐시 제공 + "OO일 기준 데이터" 날짜 명시 |
| 3순위 | 캐시 7일 초과 | 숫자 숨기고 "데이터 갱신 중" 표시 |

**"실시간 데이터"라는 인상을 절대 주지 않는다. 날짜 명시가 신뢰를 만든다.**

---

## 신규 파일 생성 위치

```
services/reaction_pipeline.py   — 이슈×반응 배치 파이프라인 (신규)
services/letter_service.py      — SendGrid 편지 발송 (신규)
routers/issues.py               — /api/issues 엔드포인트 (신규)
routers/letters.py              — /api/letters 엔드포인트 (신규)
mvp/index.html                  — MVP 프론트엔드 단일 파일 (신규)
```

---

## Supabase 테이블 (신규 생성 필요)

```sql
-- issue_reactions: 이슈별 의원 반응
CREATE TABLE issue_reactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_id UUID REFERENCES issues(id),
  member_id VARCHAR,
  stance VARCHAR CHECK (stance IN ('찬성', '반대', '침묵', '수집중')),
  confidence FLOAT,
  summary TEXT,          -- 30자 이내 AI 요약
  evidence TEXT,         -- 근거 발언 50자 이내
  data_date DATE NOT NULL,
  generated_at TIMESTAMPTZ DEFAULT now()
);

-- issues: 이슈맨 수집 이슈
CREATE TABLE issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR NOT NULL,
  source_url TEXT,
  committee VARCHAR,
  keywords TEXT[],
  collected_at TIMESTAMPTZ DEFAULT now()
);

-- letters: 시민 편지
CREATE TABLE letters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id VARCHAR NOT NULL,
  issue_id UUID,          -- 이슈 연결 (선택)
  content TEXT NOT NULL,
  nickname VARCHAR DEFAULT '시민',
  status VARCHAR DEFAULT 'pending',  -- pending/sent/blocked
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 환경 변수 추가 필요

```env
SENDGRID_API_KEY=sg.xxxx
LETTER_FROM_EMAIL=noreply@jeongchaek.ai
LETTER_FROM_NAME=정책AI 시민편지
```

---

## GPT 프롬프트 — 반응 분류 (그대로 사용)

```python
STANCE_CLASSIFICATION_PROMPT = """
당신은 국회 발언 분석가입니다.

정책 이슈: {issue_title}
의원 발언 목록: {speeches}

분류 기준:
- "찬성": 긍정적 지지 발언이 명확한 경우
- "반대": 부정적 반대 발언이 명확한 경우
- "침묵": 관련 발언 없거나 중립적인 경우

반드시 JSON으로만 응답:
{
  "stance": "찬성|반대|침묵",
  "confidence": 0.0~1.0,
  "summary": "한 줄 요약 30자 이내",
  "evidence": "근거 발언 원문 50자 이내 (없으면 null)"
}

주의: 확실하지 않으면 침묵으로 분류. 과도한 추론 금지.
"""
```

## GPT 프롬프트 — 편지 필터 (그대로 사용)

```python
LETTER_FILTER_PROMPT = """
다음 편지가 의원실 발송에 적합한지 판단하세요.

편지: {content}

차단 기준 (하나라도 해당되면 blocked=true):
- 욕설, 비속어, 혐오 표현
- 특정인에 대한 명백한 허위 사실
- 스팸성 반복 내용 또는 무의미한 텍스트
- 100자 미만의 너무 짧은 내용

JSON으로만 응답:
{"blocked": true/false, "reason": "차단 이유 (blocked일 때만)"}
"""
```

---

## 편지 이메일 템플릿

```
수신: {의원실 공식 이메일}  ← Assembly API ALLNAMEMBER에서 조회
발신: noreply@jeongchaek.ai
제목: [정책AI 시민편지] {의원명} 의원님께

안녕하세요, {의원명} 의원님.
정책AI 플랫폼을 통해 지역구 시민의 편지가 전달됩니다.

---
보낸 사람: {닉네임} (광주 {지역구} 시민)
관련 정책: {이슈 제목}

{편지 내용}
---

정책AI(jeongchaek.ai) 시민 참여 플랫폼을 통해 발송됐습니다.
회신은 이 이메일로 보내주시면 시민에게 전달됩니다.
```

---

## "전달됨" 화면 — 반드시 이 요소 포함

```
✓ 전달됐습니다
  {의원명} 의원실에 방금 편지가 전달됐어요
  {날짜 시간}
  편지 번호 #{누적번호}

  지금까지 광주 시민 총 {누적건수}건의 편지를 보냈어요

  [이미지로 저장]  [링크 복사]
  [다른 이슈 보기]
```

누적 카운터와 이미지 저장이 바이럴의 핵심이다. 절대 빠뜨리지 않는다.

---

## Phase 개발 순서

```
Week 1-2: 데이터
  - Assembly API 광주 8개 의원 이메일 검증
  - 위원회 키워드 딕셔너리 완성
  - Supabase 3개 테이블 생성

Week 3-4: 백엔드
  - reaction_pipeline.py 완성
  - letter_service.py + SendGrid 연동
  - /api/issues, /api/letters 엔드포인트

Week 5: 프론트엔드 + QA
  - mvp/index.html 5개 화면
  - 모바일 390px 레이아웃 검증
  - 편지 end-to-end 실제 발송 테스트
```

---

## 출시 기준 (이걸 만족해야 홍보 시작)

```
✓ 광주 8개 지역구 의원 이메일 발송 테스트 전원 성공
✓ 이슈맨 이슈 → 의원 반응 최소 5건 매핑 완료
✓ 스팸 필터 테스트 10건 통과
✓ AI 반응 분류 수동 검토 10건 완료
✓ 모든 요약에 "AI 생성" 명시 + "오류 신고" 링크 부착
✓ data_date 모든 화면 표시
✓ 모바일 390px 레이아웃 깨지지 않음
```

---

## 상세 PRD 참조

전체 기능 명세, API 설계, 화면 설계는 아래 파일 참조:

```
.claude/jeongchaek_ai_MVP_PRD.md
```

---

*CLAUDE.md 버전: v1.0 | 최종 수정: 2026-04-08*
