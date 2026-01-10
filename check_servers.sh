#!/bin/bash

echo "=== 서버 상태 확인 ==="
echo ""

# 프론트엔드 서버 확인
echo "1. 프론트엔드 서버 (포트 3000) 확인:"
if lsof -ti:3000 > /dev/null 2>&1; then
    echo "   ✅ 프론트엔드 서버가 실행 중입니다"
    lsof -ti:3000 | head -1 | xargs ps -p
else
    echo "   ❌ 프론트엔드 서버가 실행되지 않았습니다"
fi

echo ""

# 백엔드 서버 확인
echo "2. 백엔드 서버 (포트 8000) 확인:"
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "   ✅ 백엔드 서버가 실행 중입니다"
    lsof -ti:8000 | head -1 | xargs ps -p
else
    echo "   ❌ 백엔드 서버가 실행되지 않았습니다"
fi

echo ""
echo "=== 서버 시작 방법 ==="
echo ""
echo "프론트엔드 서버 시작:"
echo "  cd client && npm run dev"
echo ""
echo "백엔드 서버 시작:"
echo "  cd server && source ../.venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""

