# Docker 배포 가이드

이 프로젝트는 **두 가지 방식**으로 Docker 배포가 가능합니다:

## 🎯 배포 방식 선택

### 1. 통합 Dockerfile (Root) ⭐ **권장**

**하나의 컨테이너에서 Client와 Server를 함께 실행**

- **파일**: `Dockerfile` (프로젝트 루트)
- **장점**: 
  - 하나의 서비스로 관리 (간단함)
  - Render에서 하나의 Web Service만 생성
  - 무료 플랜에 적합
- **단점**: 
  - 두 서비스가 하나의 컨테이너에서 실행
  - 스케일링 시 함께 스케일링됨

**사용 방법:**
```bash
# 빌드
docker build -t yeopgang-app --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 .

# 실행
docker run -p 3000:3000 -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  yeopgang-app
```

### 2. 분리된 Dockerfile (Client/Server)

**Client와 Server를 별도 컨테이너로 실행**

- **파일**: 
  - `client/Dockerfile`
  - `server/Dockerfile`
- **장점**: 
  - 서비스 분리 (마이크로서비스 아키텍처)
  - 독립적 스케일링 가능
  - 프로덕션 환경에 적합
- **단점**: 
  - 두 개의 Web Service 관리 필요
  - 무료 플랜에서는 두 서비스 모두 필요

**사용 방법:**
```bash
# docker-compose 사용 (기존 방식)
docker-compose up --build

# 또는 개별 빌드
docker build -t yeopgang-backend ./server
docker build -t yeopgang-frontend --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 ./client
```

## 📋 Render 배포

### 통합 Dockerfile 사용 시

1. Render 대시보드 → **New +** → **Web Service**
2. 설정:
   - **Dockerfile Path**: `Dockerfile`
   - **Docker Context**: `.`
3. 환경 변수:
   - `OPENAI_API_KEY`
   - `DATABASE_URL=sqlite:///./server/data/yeopgang.db`
   - `NEXT_PUBLIC_API_URL=http://localhost:8000`

### 분리된 Dockerfile 사용 시

1. **백엔드 서비스**:
   - **Dockerfile Path**: `server/Dockerfile`
   - **Docker Context**: `server`

2. **프론트엔드 서비스**:
   - **Dockerfile Path**: `client/Dockerfile`
   - **Docker Context**: `client`
   - **Environment**: `NEXT_PUBLIC_API_URL` = 백엔드 URL

## 🔧 로컬 개발

### 통합 방식

```bash
docker-compose up --build
```

### 분리 방식

기존 `docker-compose.yml`을 사용하거나, 각각 개별 실행:

```bash
# 백엔드
cd server
docker build -t yeopgang-backend .
docker run -p 8000:8000 yeopgang-backend

# 프론트엔드 (별도 터미널)
cd client
docker build -t yeopgang-frontend --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 .
docker run -p 3000:3000 yeopgang-frontend
```

## 💡 추천

- **무료 배포/데모**: 통합 Dockerfile (Root) 사용
- **프로덕션/스케일링 필요**: 분리된 Dockerfile 사용
