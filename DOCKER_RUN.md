# Docker 실행 가이드

## 사전 준비

1. **Docker 설치 확인**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **환경 변수 파일 생성**
   프로젝트 루트에 `.env` 파일을 생성하고 필요한 환경 변수를 설정하세요.
   ```bash
   # .env.example을 참고하여 .env 파일 생성
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=sqlite:///./server/data/yeopgang.db
   DATA_ROOT=server/data
   CHROMA_DB_PATH=server/data/chroma
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

## Docker 이미지 빌드

```bash
# 프로젝트 루트 디렉토리에서 실행
docker build -t yeopgang-app --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 .
```

**빌드 옵션 설명:**
- `-t yeopgang-app`: 이미지 이름을 `yeopgang-app`으로 지정
- `--build-arg NEXT_PUBLIC_API_URL=...`: Next.js 빌드 시 사용할 API URL 설정
- `.`: 현재 디렉토리를 빌드 컨텍스트로 사용

## Docker 컨테이너 실행

### 기본 실행 (데이터 영속성 없음)

```bash
docker run -d \
  --name yeopgang \
  -p 3000:3000 \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_openai_api_key_here \
  -e DATABASE_URL=sqlite:///./server/data/yeopgang.db \
  -e DATA_ROOT=server/data \
  -e CHROMA_DB_PATH=server/data/chroma \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  yeopgang-app
```

### 데이터 영속성을 위한 실행 (권장)

```bash
docker run -d \
  --name yeopgang \
  -p 3000:3000 \
  -p 8000:8000 \
  -v "$(pwd)/server/data:/app/server/data" \
  -v "$(pwd)/ref:/app/ref" \
  -e OPENAI_API_KEY=your_openai_api_key_here \
  -e DATABASE_URL=sqlite:///./server/data/yeopgang.db \
  -e DATA_ROOT=server/data \
  -e CHROMA_DB_PATH=server/data/chroma \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  yeopgang-app
```

**옵션 설명:**
- `-d`: 백그라운드 실행 (detached mode)
- `--name yeopgang`: 컨테이너 이름 지정
- `-p 3000:3000`: 프론트엔드 포트 매핑
- `-p 8000:8000`: 백엔드 포트 매핑
- `-v "$(pwd)/server/data:/app/server/data"`: 데이터 디렉토리 볼륨 마운트 (데이터 영속성)
- `-v "$(pwd)/ref:/app/ref"`: ref 디렉토리 볼륨 마운트
- `-e`: 환경 변수 설정

### .env 파일을 사용한 실행

```bash
# .env 파일이 있는 경우
docker run -d \
  --name yeopgang \
  -p 3000:3000 \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/server/data:/app/server/data" \
  -v "$(pwd)/ref:/app/ref" \
  yeopgang-app
```

## 컨테이너 관리

### 실행 중인 컨테이너 확인
```bash
docker ps
```

### 컨테이너 로그 확인
```bash
# 전체 로그
docker logs yeopgang

# 실시간 로그 (tail -f)
docker logs -f yeopgang
```

### 컨테이너 중지
```bash
docker stop yeopgang
```

### 컨테이너 시작 (중지된 경우)
```bash
docker start yeopgang
```

### 컨테이너 재시작
```bash
docker restart yeopgang
```

### 컨테이너 삭제
```bash
# 컨테이너 중지 후 삭제
docker stop yeopgang
docker rm yeopgang

# 강제 삭제 (실행 중인 경우)
docker rm -f yeopgang
```

### 컨테이너 내부 접속
```bash
docker exec -it yeopgang bash
```

## 접속 URL

컨테이너 실행 후 다음 URL로 접속할 수 있습니다:

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 문제 해결

### 포트가 이미 사용 중인 경우
다른 포트로 매핑:
```bash
docker run -d \
  --name yeopgang \
  -p 3001:3000 \
  -p 8001:8000 \
  ...
```

### 빌드 실패 시
```bash
# 캐시 없이 다시 빌드
docker build --no-cache -t yeopgang-app --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 .
```

### 컨테이너가 즉시 종료되는 경우
```bash
# 로그 확인
docker logs yeopgang

# 인터랙티브 모드로 실행하여 오류 확인
docker run -it --rm \
  -p 3000:3000 \
  -p 8000:8000 \
  --env-file .env \
  yeopgang-app
```

## Windows에서 실행

Windows PowerShell에서는 경로 형식이 다릅니다:

```powershell
# 볼륨 마운트 (Windows)
docker run -d `
  --name yeopgang `
  -p 3000:3000 `
  -p 8000:8000 `
  -v "${PWD}\server\data:/app/server/data" `
  -v "${PWD}\ref:/app/ref" `
  --env-file .env `
  yeopgang-app
```

## Docker Compose 사용 (선택사항)

더 편리한 관리를 위해 `docker-compose.yml`을 사용할 수도 있습니다:

```yaml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - NEXT_PUBLIC_API_URL=http://localhost:8000
    container_name: yeopgang-app
    ports:
      - "3000:3000"
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./server/data:/app/server/data
      - ./ref:/app/ref
    restart: unless-stopped
```

실행:
```bash
docker-compose up -d
```

중지:
```bash
docker-compose down
```
