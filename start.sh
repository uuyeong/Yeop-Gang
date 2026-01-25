#!/bin/bash
set -e

echo "🚀 서비스 시작 중..."

# 백엔드 서버 시작 (백그라운드)
cd /app/server
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ 백엔드 서버 시작 (PID: $BACKEND_PID)"

# 잠시 대기 (백엔드가 시작될 시간)
sleep 2

# 프론트엔드 서버 시작 (백그라운드)
cd /app/client
NODE_ENV=production PORT=3000 node server.js &
FRONTEND_PID=$!
echo "✅ 프론트엔드 서버 시작 (PID: $FRONTEND_PID)"

echo "✅ 모든 서비스가 시작되었습니다"
echo "   - 프론트엔드: http://localhost:3000"
echo "   - 백엔드 API: http://localhost:8000"

# 프로세스 종료 시그널 처리
trap "echo '종료 시그널 수신...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGTERM SIGINT

# 프로세스가 종료될 때까지 대기
wait $BACKEND_PID $FRONTEND_PID
