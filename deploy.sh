#!/bin/bash
# Render 배포를 위한 간단한 스크립트

echo "🚀 Render 배포 준비 체크리스트"
echo "================================"
echo ""

# 1. Dockerfile 확인
echo "✅ 1. Dockerfile 확인 중..."
if [ -f "server/Dockerfile" ] && [ -f "client/Dockerfile" ]; then
    echo "   ✓ server/Dockerfile 존재"
    echo "   ✓ client/Dockerfile 존재"
else
    echo "   ✗ Dockerfile이 없습니다!"
    exit 1
fi

# 2. 환경 변수 확인
echo ""
echo "✅ 2. 환경 변수 확인 중..."
if [ -f ".env.example" ]; then
    echo "   ✓ .env.example 존재"
    echo "   ⚠️  Render 대시보드에서 다음 환경 변수를 설정하세요:"
    echo "      - OPENAI_API_KEY (백엔드)"
    echo "      - NEXT_PUBLIC_API_URL (프론트엔드)"
else
    echo "   ⚠️  .env.example이 없습니다"
fi

# 3. Git 상태 확인
echo ""
echo "✅ 3. Git 상태 확인 중..."
if [ -d ".git" ]; then
    echo "   ✓ Git 저장소 확인됨"
    echo "   현재 브랜치: $(git branch --show-current)"
    echo "   커밋되지 않은 변경사항:"
    git status --short || echo "      (없음)"
else
    echo "   ⚠️  Git 저장소가 아닙니다"
fi

# 4. 로컬 빌드 테스트 (선택사항)
echo ""
read -p "로컬에서 Docker 빌드 테스트를 진행하시겠습니까? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔨 백엔드 빌드 테스트 중..."
    docker build -t yeopgang-backend-test ./server
    if [ $? -eq 0 ]; then
        echo "   ✓ 백엔드 빌드 성공"
    else
        echo "   ✗ 백엔드 빌드 실패"
    fi
    
    echo ""
    echo "🔨 프론트엔드 빌드 테스트 중..."
    docker build -t yeopgang-frontend-test --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 ./client
    if [ $? -eq 0 ]; then
        echo "   ✓ 프론트엔드 빌드 성공"
    else
        echo "   ✗ 프론트엔드 빌드 실패"
    fi
fi

echo ""
echo "================================"
echo "📋 다음 단계:"
echo "1. GitHub에 코드 푸시"
echo "2. Render 대시보드에서 Web Service 생성"
echo "3. Dockerfile 경로 설정:"
echo "   - 백엔드: server/Dockerfile"
echo "   - 프론트엔드: client/Dockerfile"
echo "4. 환경 변수 설정"
echo ""
echo "자세한 내용은 DEPLOYMENT.md를 참고하세요."
