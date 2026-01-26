#!/bin/bash
set -e

echo "🚀 서비스 시작 중..."

# Render는 PORT 환경 변수를 제공하므로 사용 (없으면 기본값 3000)
FRONTEND_PORT=${PORT:-3000}
BACKEND_PORT=8000

# 백엔드 서버 시작 (백그라운드, 내부 포트)
cd /app/server
uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!
echo "✅ 백엔드 서버 시작 (PID: $BACKEND_PID) - 포트: $BACKEND_PORT"

# 백엔드가 준비될 때까지 대기 (최대 30초)
echo "⏳ 백엔드 서버 준비 대기 중..."
MAX_WAIT=30
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
  if curl -f -s http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
    echo "✅ 백엔드 서버 준비 완료"
    break
  fi
  WAIT_COUNT=$((WAIT_COUNT + 1))
  sleep 1
  if [ $((WAIT_COUNT % 5)) -eq 0 ]; then
    echo "   대기 중... ($WAIT_COUNT/$MAX_WAIT)"
  fi
done

if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
  echo "⚠️  백엔드 서버가 $MAX_WAIT초 내에 준비되지 않았습니다. 계속 진행합니다..."
fi

# 프론트엔드 서버 시작 (Render가 할당한 포트 사용)
cd /app/client
PORT=$FRONTEND_PORT HOSTNAME="0.0.0.0" node server.js &
FRONTEND_PID=$!
echo "✅ 프론트엔드 서버 시작 (PID: $FRONTEND_PID) - 포트: $FRONTEND_PORT"

echo "✅ 모든 서비스가 시작되었습니다"
echo "   - 프론트엔드: http://0.0.0.0:$FRONTEND_PORT"
echo "   - 백엔드 API: http://localhost:$BACKEND_PORT (내부 전용)"

# 프로세스 종료 시그널 처리
trap "echo '종료 시그널 수신...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGTERM SIGINT

# 프로세스가 종료될 때까지 대기
wait $BACKEND_PID $FRONTEND_PID
