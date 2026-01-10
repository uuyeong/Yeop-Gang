#!/bin/bash
# 백엔드와 프론트엔드 서버를 실행하는 스크립트

echo "🚀 서버 실행 스크립트"
echo "===================="

# 프로젝트 루트로 이동
cd "$(dirname "$0")"

# 백엔드 서버 실행 (백그라운드)
echo ""
echo "📡 백엔드 서버 시작 중..."
cd server
source ../.venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 백엔드 서버 실행 중 (PID: $BACKEND_PID)"
echo "   로그: backend.log"
echo "   URL: http://localhost:8000"

# 잠시 대기
sleep 2

# 프론트엔드 서버 실행 (백그라운드)
echo ""
echo "🎨 프론트엔드 서버 시작 중..."
cd ../client
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 프론트엔드 서버 실행 중 (PID: $FRONTEND_PID)"
echo "   로그: frontend.log"
echo "   URL: http://localhost:3000"

echo ""
echo "===================="
echo "✅ 서버 실행 완료!"
echo ""
echo "📝 접속 URL:"
echo "   - 프론트엔드: http://localhost:3000/student/play/test-course-1"
echo "   - 백엔드 API: http://localhost:8000/docs"
echo ""
echo "🛑 서버 종료 방법:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   또는: pkill -f 'uvicorn main:app' && pkill -f 'next dev'"
echo ""
echo "📋 로그 확인:"
echo "   tail -f backend.log    # 백엔드 로그"
echo "   tail -f frontend.log   # 프론트엔드 로그"

