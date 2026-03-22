# 🚀 AI 정당 빠른 시작 가이드

## 📋 목차
1. [시스템 요구사항](#시스템-요구사항)
2. [설치](#설치)
3. [실행](#실행)
4. [테스트](#테스트)
5. [다음 단계](#다음-단계)

---

## 🖥️ 시스템 요구사항

- Python 3.9 이상
- pip
- 인터넷 연결

---

## 📥 설치

### 1단계: 환경 변수 설정

```bash
cd ai-political-party
cp config/.env.example config/.env
```

`.env` 파일을 열고 다음 항목을 입력하세요:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

**API 키 발급:**
- Anthropic: https://console.anthropic.com/

### 2단계: 빠른 시작 스크립트 실행

```bash
./start.sh
```

그러면 자동으로:
- ✅ Python 가상환경 생성
- ✅ 필요한 패키지 설치
- ✅ 실행 옵션 제공

---

## 🎯 실행

### 옵션 1: 오케스트레이터 테스트

```bash
python agents/orchestrator.py
```

**결과:**
- 일일 브리핑 자동 생성
- 시스템 상태 확인
- `data/outputs/` 폴더에 결과물 저장

### 옵션 2: 챗봇 테스트

```bash
python agents/support_agent.py
```

**결과:**
- 다양한 질문에 AI 응답 테스트
- FAQ 자동 응답 확인

### 옵션 3: 전체 시스템 실행

```bash
./start.sh
# 메뉴에서 "4" 선택
```

**실행되는 것들:**
- 🚀 FastAPI 백엔드 서버 (포트 8000)
- 🤖 AI 에이전트들

**접속:**
- API 문서: http://localhost:8000/docs
- 웹사이트: `web/frontend/index.html` 파일을 브라우저에서 열기

---

## 🧪 테스트

### API 테스트 (curl)

```bash
# 상태 확인
curl http://localhost:8000/api/status

# 챗봇 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "당원 가입 방법이 궁금해요"}'

# 통계 확인
curl http://localhost:8000/api/stats
```

### 웹사이트 테스트

1. API 서버가 실행중인지 확인 (포트 8000)
2. `web/frontend/index.html` 파일을 브라우저에서 열기
3. 챗봇에 메시지 입력해보기

---

## 📊 생성된 파일 확인

실행 후 다음 위치에서 결과물을 확인할 수 있습니다:

```
data/
├── logs/
│   ├── orchestrator_*.log      # 시스템 로그
│   └── hourly_*.json           # 작업 로그
└── outputs/
    ├── briefing_*.md           # 일일 브리핑
    └── strategy_week_*.md      # 주간 전략 보고서
```

---

## 🎯 다음 단계

### Phase 1 완료 체크리스트

- [x] ✅ 중앙 오케스트레이터 작동
- [x] ✅ 챗봇 에이전트 작동
- [x] ✅ 기본 웹사이트 완성
- [x] ✅ API 서버 실행

### Phase 2 계획

다음으로 만들 에이전트:
1. **마케팅팀 에이전트** - SNS 자동 포스팅
2. **데이터분석팀 에이전트** - 통계 및 분석
3. **정책개발팀 에이전트** - 정책 제안 분석

---

## 🆘 문제 해결

### 문제: 패키지 설치 오류
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 문제: API 키 오류
- `.env` 파일에 `ANTHROPIC_API_KEY`가 올바르게 입력되었는지 확인
- API 키에 따옴표가 없는지 확인

### 문제: 포트 8000이 이미 사용 중
```bash
# 다른 포트 사용
python web/backend/main.py --port 8001
```

---

## 📞 지원

- GitHub Issues: 문제 보고 및 질문
- 이메일: info@ai-party.kr

---

**마지막 업데이트**: 2026년 2월 2일  
**버전**: 0.1.0
