# PRD: 민주AI 듀얼 플랫폼 (웹 + Flutter 앱)

**버전**: 1.0
**작성일**: 2026-03-22
**프로젝트명**: 민주AI — AI 기반 투명한 정당 운영 플랫폼
**목표**: 2028년 4월 국회의원 선거 10석 당선 (지역구 3 + 비례대표 7)

---

## 1. 제품 개요

### 1.1 한 줄 요약
AI 에이전트 7개가 자율 운영하는 정당 플랫폼을 **웹(PWA)** + **Flutter 네이티브 앱**으로 시민에게 제공한다.

### 1.2 현재 상태 (AS-IS)
| 항목 | 상태 |
|------|------|
| 백엔드 | FastAPI (main.py, 299줄) — 로컬 실행만 가능 |
| 프론트엔드 | index.html 1개 파일 (685줄, 인라인 CSS+JS) |
| 데이터 저장 | JSON 파일 (DB 없음) |
| 인증 | 없음 |
| 호스팅 | 로컬 (localhost:8000) |
| AI 에이전트 | 7개 구현 완료 (챗봇, 분석, 정책, 마케팅, 모니터링, 오케스트레이터, 배치) |
| 회원 데이터 | 14,764명 (JSON) |

### 1.3 목표 상태 (TO-BE)
| 항목 | 목표 |
|------|------|
| 웹 | PWA (모바일 설치 가능) — Vercel 배포 |
| 앱 | Flutter (Android + iOS) — Google Play + App Store |
| 백엔드 | FastAPI 클라우드 배포 (Railway/Render) |
| DB | Supabase (PostgreSQL) |
| 인증 | JWT + OAuth2 (카카오/구글/애플 로그인) |
| 푸시 알림 | FCM (Android) + APNs (iOS) |

---

## 2. 타겟 사용자

### 2.1 주요 사용자
| 페르소나 | 설명 | 비중 |
|----------|------|------|
| **정치 관심 청년** | 20~30대, 새로운 정치 방식에 관심 | 55% |
| **기독교 시민** | 말씀 기반 정치 공동체에 공감 | 25% |
| **정책 참여자** | 직접 정책 제안/투표하고 싶은 시민 | 15% |
| **당 운영자** | 1인 대표 (관리자 대시보드) | 5% |

### 2.2 사용 환경
- 모바일 70% / 데스크톱 30% (한국 정치 사이트 평균)
- Android 65% / iOS 35% (한국 시장)
- 웹 브라우저: Chrome 60% / Safari 25% / 기타 15%

---

## 3. 핵심 기능 (Features)

### 3.1 Phase 1 — 백엔드 정비 (공통 기반)

| ID | 기능 | 설명 | 우선순위 | 상태 |
|----|------|------|----------|------|
| BE-01 | DB 전환 | JSON → Supabase PostgreSQL 마이그레이션 | P0 | 미착수 |
| BE-02 | 인증 시스템 | JWT 발급 + 카카오/구글/애플 OAuth2 | P0 | 미착수 |
| BE-03 | API 보안 | CORS 도메인 제한, Rate Limiting, HTTPS | P0 | 미착수 |
| BE-04 | 클라우드 배포 | Railway 또는 Render에 FastAPI 배포 | P0 | 미착수 |
| BE-05 | 환경변수 분리 | API 키 안전 관리 (Secret Manager) | P0 | 미착수 |
| BE-06 | 푸시 알림 API | FCM + APNs 통합 알림 엔드포인트 | P1 | 미착수 |

### 3.2 Phase 2 — 웹 프론트엔드 (PWA)

| ID | 기능 | 설명 | 우선순위 | 상태 |
|----|------|------|----------|------|
| WEB-01 | Next.js 전환 | index.html → Next.js App Router 프로젝트 | P0 | 미착수 |
| WEB-02 | PWA 설정 | manifest.json + Service Worker + 오프라인 캐시 | P0 | 미착수 |
| WEB-03 | 반응형 디자인 | 모바일/태블릿/데스크톱 완전 대응 | P0 | 미착수 |
| WEB-04 | 로그인/회원가입 | 카카오/구글 소셜 로그인 UI | P0 | 미착수 |
| WEB-05 | 챗봇 UI 개선 | 타이핑 인디케이터, 대화 히스토리 저장 | P1 | 미착수 |
| WEB-06 | 정책 투표 UI | 실시간 투표 + 결과 시각화 (차트) | P1 | 미착수 |
| WEB-07 | 대시보드 | 관리자 전용 운영 대시보드 | P2 | 미착수 |
| WEB-08 | SEO 최적화 | 메타태그, 시맨틱 HTML, OG 태그 | P1 | 미착수 |
| WEB-09 | 다크모드 | 시스템 설정 연동 다크모드 | P2 | 미착수 |
| WEB-10 | Vercel 배포 | CI/CD + 커스텀 도메인 연결 | P0 | 미착수 |

### 3.3 Phase 3 — Flutter 네이티브 앱

| ID | 기능 | 설명 | 우선순위 | 상태 |
|----|------|------|----------|------|
| APP-01 | Flutter 프로젝트 생성 | 프로젝트 구조 + 네비게이션 | P0 | 미착수 |
| APP-02 | 로그인/회원가입 | 카카오/구글/애플 소셜 로그인 | P0 | 미착수 |
| APP-03 | 홈 화면 | 통계, 최신 정책, 빠른 메뉴 | P0 | 미착수 |
| APP-04 | AI 챗봇 | 실시간 대화 UI (말풍선, 타이핑 인디케이터) | P0 | 미착수 |
| APP-05 | 정책 목록/상세 | 정책 카드 리스트 + 상세 보기 + 투표 | P0 | 미착수 |
| APP-06 | 정책 제안 | 폼 제출 + AI 분석 결과 표시 | P0 | 미착수 |
| APP-07 | 푸시 알림 | FCM 연동 (정책 업데이트, 투표 알림) | P1 | 미착수 |
| APP-08 | 국회의원 모니터링 | 의원 카드 + 활동 점수 + 상세 | P1 | 미착수 |
| APP-09 | 마이페이지 | 프로필, 내 제안, 투표 이력, 설정 | P1 | 미착수 |
| APP-10 | 오프라인 모드 | 캐시된 정책/통계 오프라인 열람 | P2 | 미착수 |
| APP-11 | 접근성 | 스크린리더, 폰트 크기 조절, 고대비 | P1 | 미착수 |
| APP-12 | 딥링크 | 웹 URL → 앱 자동 연결 | P2 | 미착수 |

### 3.4 Phase 4 — 스토어 출시 준비

| ID | 기능 | 설명 | 우선순위 | 상태 |
|----|------|------|----------|------|
| STORE-01 | 개인정보 처리방침 | 웹페이지 + 앱 내 링크 (필수) | P0 | 미착수 |
| STORE-02 | 이용약관 | 서비스 이용약관 페이지 | P0 | 미착수 |
| STORE-03 | 앱 아이콘/스플래시 | 1024x1024 아이콘 + 스플래시 스크린 | P0 | 미착수 |
| STORE-04 | 스크린샷 | 각 스토어별 스크린샷 5~8장 | P0 | 미착수 |
| STORE-05 | 앱 설명문 | 한국어/영어 앱 설명 | P0 | 미착수 |
| STORE-06 | 연령 등급 | 17+ (정치 관련 콘텐츠) | P0 | 미착수 |
| STORE-07 | 정치 앱 사전 승인 | Apple 정치 앱 가이드라인 대응 | P0 | 미착수 |
| STORE-08 | Google Play 등록 | $25 일회성 비용, AAB 업로드 | P0 | 미착수 |
| STORE-09 | App Store 등록 | $99/년, Apple Developer 가입 | P0 | 미착수 |
| STORE-10 | 앱 심사 대응 | 리젝 시 대응 문서 준비 | P1 | 미착수 |

---

## 4. 기술 스택

### 4.1 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                    Supabase (PostgreSQL)                  │
│              회원 / 정책 / 투표 / 대화 이력                 │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│              FastAPI 백엔드 (Railway/Render)               │
│                                                           │
│  ┌─────────┬─────────┬──────────┬──────────┬───────────┐ │
│  │Support  │Analytics│ Policy   │Marketing │Monitoring  │ │
│  │Agent    │Agent    │ Agent    │Agent     │Agent       │ │
│  └─────────┴─────────┴──────────┴──────────┴───────────┘ │
│                                                           │
│  ┌──────────────┬────────────┬─────────────────────────┐ │
│  │ JWT 인증     │ Rate Limit │ FCM/APNs 푸시 알림       │ │
│  └──────────────┴────────────┴─────────────────────────┘ │
└──────────────┬──────────────────────────┬────────────────┘
               │          REST API         │
     ┌─────────▼─────────┐     ┌──────────▼──────────┐
     │   Next.js (PWA)    │     │   Flutter App        │
     │                    │     │                      │
     │  - Vercel 배포      │     │  - Android (AAB)     │
     │  - SSR/SSG         │     │  - iOS (IPA)         │
     │  - Service Worker  │     │  - FCM 푸시           │
     │  - 오프라인 캐시     │     │  - 딥링크             │
     └────────────────────┘     └──────────────────────┘
```

### 4.2 기술 선택 근거

| 레이어 | 기술 | 이유 |
|--------|------|------|
| **웹 프론트** | Next.js 14+ (App Router) | SSR/SSG, SEO, PWA 지원, Vercel 최적화 |
| **모바일 앱** | Flutter 3.x | 단일 코드베이스로 Android+iOS, 네이티브 성능, 한국 커뮤니티 활발 |
| **백엔드** | FastAPI (유지) | 기존 코드 활용, 비동기 성능, 자동 API 문서 |
| **DB** | Supabase | 무료 티어, PostgreSQL, 실시간 구독, Row Level Security |
| **인증** | Supabase Auth + JWT | 카카오/구글/애플 OAuth 내장, 토큰 관리 |
| **호스팅** | Railway (백엔드) + Vercel (웹) | 자동 배포, 무료~저비용, 한국 리전 |
| **푸시** | Firebase Cloud Messaging | Android+iOS 통합, 무료 |
| **AI** | Anthropic Claude API (유지) | 기존 에이전트 코드 그대로 활용 |

---

## 5. DB 스키마 (Supabase 마이그레이션)

### 5.1 핵심 테이블

```sql
-- 회원
CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    region TEXT,              -- 지역 (서울, 경기 등)
    age_group TEXT,           -- 연령대
    auth_provider TEXT,       -- kakao, google, apple
    role TEXT DEFAULT 'member', -- member, admin
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 정책 제안
CREATE TABLE proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,   -- 경제, 복지, 교육, 환경, 교통
    proposer_id UUID REFERENCES members(id),
    status TEXT DEFAULT '검토중', -- 검토중, 분석완료, 투표중, 채택, 반려
    feasibility_score INT,
    analysis JSONB,           -- AI 분석 결과
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 투표
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID REFERENCES proposals(id),
    member_id UUID REFERENCES members(id),
    vote_type TEXT NOT NULL,  -- for, against
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(proposal_id, member_id) -- 1인 1투표
);

-- 대화 이력
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID REFERENCES members(id),
    messages JSONB NOT NULL,  -- [{role, content, timestamp}]
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 국회의원 모니터링
CREATE TABLE lawmakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    party TEXT,
    district TEXT,
    region TEXT,
    bills_proposed INT DEFAULT 0,
    attendance_rate FLOAT DEFAULT 0,
    promise_fulfillment FLOAT DEFAULT 0,
    vulnerability_score FLOAT DEFAULT 0,
    data JSONB,               -- 상세 활동 데이터
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 푸시 알림 토큰
CREATE TABLE push_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID REFERENCES members(id),
    token TEXT NOT NULL,
    platform TEXT NOT NULL,   -- android, ios, web
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 6. API 엔드포인트 (개선)

### 6.1 인증
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/auth/login` | 소셜 로그인 (카카오/구글/애플) |
| POST | `/api/auth/refresh` | JWT 토큰 갱신 |
| POST | `/api/auth/logout` | 로그아웃 |
| GET | `/api/auth/me` | 내 정보 조회 |

### 6.2 회원
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/members/profile` | 프로필 조회 |
| PUT | `/api/members/profile` | 프로필 수정 |
| GET | `/api/members/stats` | 회원 통계 |

### 6.3 정책 (기존 개선)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/policies` | 정책 목록 (페이지네이션) |
| GET | `/api/policies/{id}` | 정책 상세 |
| POST | `/api/policies` | 정책 제안 (인증 필요) |
| POST | `/api/policies/{id}/analyze` | AI 분석 |
| POST | `/api/policies/{id}/vote` | 투표 (인증 필요) |
| GET | `/api/policies/{id}/votes` | 투표 현황 |

### 6.4 챗봇 (기존 유지)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat` | 대화 (기존 유지) |
| GET | `/api/chat/history` | 대화 이력 (인증 필요) |
| GET | `/api/faq` | FAQ 목록 |

### 6.5 분석/모니터링 (기존 유지)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/analytics/trends` | 트렌드 |
| GET | `/api/analytics/predictions` | 선거 예측 |
| GET | `/api/lawmakers` | 국회의원 목록 |
| GET | `/api/lawmakers/{id}` | 국회의원 상세 |

### 6.6 알림 (신규)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/push/register` | 푸시 토큰 등록 |
| DELETE | `/api/push/unregister` | 푸시 토큰 삭제 |

---

## 7. 화면 구성 (Screens)

### 7.1 공통 (웹 + 앱)

```
1. 스플래시/로딩
2. 로그인 (카카오/구글/애플)
3. 홈
   ├── 실시간 통계 카드
   ├── 최신 정책 3개
   └── 빠른 메뉴 (챗봇, 제안, 모니터링)
4. 정책 목록
   ├── 카테고리 필터
   ├── 정책 카드 리스트
   └── 투표 버튼
5. 정책 상세
   ├── 제목/내용/카테고리
   ├── AI 분석 결과 (점수, 장단점)
   ├── 투표 현황 (차트)
   └── 댓글 (향후)
6. 정책 제안
   ├── 제목 입력
   ├── 내용 입력
   ├── 카테고리 선택
   └── AI 분석 요청
7. AI 챗봇
   ├── 대화 UI (말풍선)
   ├── FAQ 빠른 버튼
   └── 대화 이력
8. 국회의원 모니터링
   ├── 의원 카드 리스트
   ├── 활동 점수
   └── 상세 보기
9. 마이페이지
   ├── 프로필
   ├── 내 정책 제안
   ├── 투표 이력
   ├── 알림 설정
   └── 로그아웃
```

### 7.2 디자인 시스템

| 항목 | 값 |
|------|-----|
| 주 색상 | `#667EEA` (보라-파랑 그라데이션) |
| 보조 색상 | `#764BA2` |
| 배경 | `#F8F9FA` (라이트) / `#1A1A2E` (다크) |
| 폰트 | Pretendard (한글) + Inter (영문) |
| 모서리 | 12px (카드), 8px (버튼), 50% (아바타) |
| 그림자 | `0 4px 6px rgba(0,0,0,0.1)` |

---

## 8. 비기능 요구사항 (NFR)

| 항목 | 요구사항 |
|------|----------|
| **성능** | 앱 최초 로딩 3초 이내, API 응답 500ms 이내 (챗봇 제외) |
| **가용성** | 99.5% 업타임 (월 3.6시간 다운타임 허용) |
| **보안** | HTTPS 필수, JWT 만료 24h, Refresh Token 30일 |
| **접근성** | WCAG 2.1 AA 수준, 스크린리더 지원 |
| **다국어** | 1차: 한국어만 / 2차: 영어 추가 |
| **오프라인** | 마지막 로드된 정책/통계 캐시 열람 가능 |
| **분석** | Firebase Analytics (앱) + Google Analytics (웹) |

---

## 9. 스토어 심사 대응

### 9.1 Apple App Store 주의사항

| 가이드라인 | 대응 방안 |
|-----------|----------|
| **4.2 Minimum Functionality** | 웹뷰 래핑 금지 → Flutter 네이티브 UI 사용 |
| **1.2 User Generated Content** | 정책 제안 = UGC → 신고/차단 기능 필수 |
| **5.1 Privacy** | 개인정보 처리방침 + App Privacy Labels 제출 |
| **Political Apps** | 정치 앱 사전 심사 요청, 운영 주체 명확히 기재 |
| **Sign in with Apple** | 소셜 로그인 제공 시 Apple 로그인 필수 포함 |

### 9.2 Google Play 주의사항

| 정책 | 대응 방안 |
|------|----------|
| **Elections Ads** | 선거 광고 투명성 정책 준수 |
| **Data Safety** | 데이터 수집 항목 정직하게 선언 |
| **Target SDK** | Android 14 (API 34) 이상 타겟 |
| **Content Rating** | IARC 등급 설정 (Mature 17+) |

---

## 10. 일정 (예상)

```
Week 1-2:  [Phase 1] 백엔드 정비
           - Supabase 셋업 + DB 마이그레이션
           - JWT 인증 시스템
           - API 보안 + 클라우드 배포

Week 3-4:  [Phase 2] 웹 프론트엔드
           - Next.js 프로젝트 전환
           - PWA 설정
           - Vercel 배포

Week 5-7:  [Phase 3] Flutter 앱 개발
           - 프로젝트 구조 + 네비게이션
           - 핵심 화면 (홈, 정책, 챗봇, 로그인)
           - 푸시 알림

Week 8:    [Phase 4] 스토어 출시 준비
           - 개인정보 처리방침 / 이용약관
           - 앱 아이콘 / 스크린샷
           - Google Play + App Store 제출
           - 심사 대응
```

---

## 11. 비용 (월간 예상)

| 항목 | 비용 | 비고 |
|------|------|------|
| Claude API | $500~1,000 | 기존 유지 |
| Supabase | $0~25 | 무료 티어 → Pro |
| Railway (백엔드) | $5~20 | 사용량 기반 |
| Vercel (웹) | $0 | 무료 티어 |
| Firebase (푸시) | $0 | 무료 |
| Apple Developer | $99/년 | 필수 |
| Google Play | $25 (1회) | 필수 |
| 도메인 | $10~20/년 | 선택 |
| **총 월간** | **$530~1,070** | |

---

## 12. 리스크 & 대응

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| Apple 심사 리젝 (정치 앱) | 높음 | 높음 | 사전 심사 요청, 네이티브 기능 충분히 포함, 운영 주체 명확히 |
| Claude API 비용 초과 | 중간 | 중간 | Batch API + 캐싱으로 비용 최적화 (이미 구현) |
| 동시 접속 부하 | 낮음 | 중간 | Supabase 연결 풀링 + API Rate Limiting |
| 개인정보 유출 | 낮음 | 높음 | Supabase RLS + 최소 수집 원칙 + 암호화 |
| 정치 콘텐츠 논란 | 중간 | 중간 | 콘텐츠 모더레이션 정책 + 신고 기능 |

---

## 13. 성공 지표 (KPI)

| 지표 | 목표 (6개월) |
|------|-------------|
| 앱 다운로드 | 10,000+ |
| 웹 MAU | 5,000+ |
| 정책 제안 수 | 500+ |
| 투표 참여율 | 회원의 30%+ |
| 앱 평점 | 4.0+ (5점 만점) |
| 챗봇 응답 만족도 | 80%+ |
| 당원 전환율 (방문→가입) | 15%+ |

---

## 14. 이해관계자

| 역할 | 담당 | 책임 |
|------|------|------|
| 대표/PM | 1인 운영 | 최종 의사결정, 정치 콘텐츠 승인 |
| AI 개발 | Claude Code | 코드 구현, 기술 의사결정 |
| 디자인 | AI 생성 + 수동 조정 | UI/UX, 앱 아이콘, 스크린샷 |
| 법률 | 외부 자문 | 개인정보 처리방침, 정치자금법 검토 |

---

## 부록: 기존 AI 에이전트 현황

| 에이전트 | 파일 | 줄 수 | 역할 | 활용 |
|----------|------|-------|------|------|
| Orchestrator | orchestrator.py | 494 | 중앙 제어, 스케줄링 | 백엔드 유지 |
| Support | support_agent.py | 337 | 24/7 챗봇 | 웹+앱 공용 API |
| Analytics | analytics_agent.py | 659 | 데이터 분석, 예측 | 웹+앱 공용 API |
| Policy | policy_agent.py | 208 | 정책 관리, AI 분석 | 웹+앱 공용 API |
| Marketing | marketing_agent.py | 583 | SNS 자동화 | 백엔드 자율 운영 |
| Monitoring | monitoring_agent.py | 735 | 국회의원 감시 | 웹+앱 공용 API |
| Batch | batch_helper.py | 193 | 비용 최적화 | 백엔드 내부 |
