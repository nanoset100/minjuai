#!/bin/bash
# AI 정당 빠른 시작 스크립트

echo "🏛️ AI 정당 시스템 시작"
echo "================================"
echo ""

# 1. Python 가상환경 확인
if [ ! -d "venv" ]; then
    echo "📦 Python 가상환경 생성 중..."
    python3 -m venv venv
fi

echo "🔧 가상환경 활성화..."
source venv/bin/activate

# 2. 패키지 설치
echo "📥 필요한 패키지 설치 중..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 3. 환경 변수 확인
if [ ! -f "config/.env" ]; then
    echo "⚠️  .env 파일이 없습니다!"
    echo "config/.env.example을 복사하여 config/.env를 만들고"
    echo "API 키를 입력해주세요."
    exit 1
fi

echo ""
echo "✅ 설정 완료!"
echo ""
echo "실행 옵션을 선택하세요:"
echo "1) 오케스트레이터 테스트"
echo "2) 챗봇 테스트"
echo "3) API 서버 실행"
echo "4) 전체 시스템 실행"
echo ""

read -p "선택 (1-4): " choice

case $choice in
    1)
        echo "🤖 오케스트레이터 테스트..."
        python agents/orchestrator.py
        ;;
    2)
        echo "💬 챗봇 테스트..."
        python agents/support_agent.py
        ;;
    3)
        echo "🚀 API 서버 실행..."
        python web/backend/main.py
        ;;
    4)
        echo "🌟 전체 시스템 실행..."
        echo "백엔드 서버를 백그라운드에서 실행합니다..."
        python web/backend/main.py &
        SERVER_PID=$!
        
        echo ""
        echo "================================"
        echo "✅ 시스템 가동 완료!"
        echo "================================"
        echo ""
        echo "📝 API 문서: http://localhost:8000/docs"
        echo "🌐 웹사이트: web/frontend/index.html 파일을 브라우저에서 열어주세요"
        echo ""
        echo "종료하려면 Ctrl+C를 누르세요"
        echo ""
        
        # 사용자가 종료할 때까지 대기
        trap "kill $SERVER_PID; echo '👋 시스템 종료'; exit" INT
        wait $SERVER_PID
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac
