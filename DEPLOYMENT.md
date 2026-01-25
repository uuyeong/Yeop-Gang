# 배포 가이드

이 문서는 Docker와 Render를 사용한 배포 방법을 설명합니다.

## 📋 목차

1. [로컬 Docker 실행](#로컬-docker-실행)
2. [Render 배포](#render-배포)
3. [환경 변수 설정](#환경-변수-설정)
4. [문제 해결](#문제-해결)

## 🐳 로컬 Docker 실행

### 사전 요구사항

- Docker Desktop 설치
- Docker Compose 설치 (Docker Desktop에 포함됨)

### 실행 방법

1. **환경 변수 설정**

   프로젝트 루트에 `.env` 파일을 생성하고 필요한 환경 변수를 설정하세요:

   ```bash
   cp .env.example .env
   # .env 파일을 편집하여 실제 값 입력
   ```

2. **Docker Compose로 실행**

   ```bash
   docker-compose up --build
   ```

   또는 백그라운드에서 실행:

   ```bash
   docker-compose up -d --build
   ```

3. **서비스 접속**

   - 프론트엔드: http://localhost:3000
   - 백엔드 API: http://localhost:8000
   - API 문서: http://localhost:8000/docs

4. **로그 확인**

   ```bash
   docker-compose logs -f
   ```

5. **서비스 중지**

   ```bash
   docker-compose down
   ```

## ☁️ Render 배포

### 사전 준비

1. [Render](https://render.com) 계정 생성
2. GitHub 저장소 연결 (또는 GitLab, Bitbucket)

### 배포 단계

#### 방법 1: render.yaml 사용 (권장)

1. **저장소에 render.yaml 커밋**

   ```bash
   git add render.yaml
   git commit -m "Add Render deployment configuration"
   git push
   ```

2. **Render 대시보드에서 Blueprint 배포**

   - Render 대시보드 접속
   - "New" → "Blueprint" 선택
   - GitHub 저장소 연결
   - Render가 `render.yaml`을 자동으로 감지하여 서비스 생성

#### 방법 2: 수동 배포

**백엔드 서비스 배포:**

1. Render 대시보드에서 "New" → "Web Service" 선택
2. GitHub 저장소 연결
3. 설정:
   - **Name**: `yeopgang-backend`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./server/Dockerfile`
   - **Docker Context**: `./server`
   - **Plan**: Free 또는 Starter (필요에 따라)
4. 환경 변수 설정 (아래 참조)
5. 디스크 추가:
   - Name: `yeopgang-data`
   - Mount Path: `/app/data`
   - Size: 1GB (필요에 따라 조정)

**프론트엔드 서비스 배포:**

1. Render 대시보드에서 "New" → "Web Service" 선택
2. GitHub 저장소 연결
3. 설정:
   - **Name**: `yeopgang-frontend`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./client/Dockerfile`
   - **Docker Context**: `./client`
   - **Plan**: Free 또는 Starter
4. 환경 변수 설정:
   - `NEXT_PUBLIC_API_URL`: 백엔드 서비스의 URL (예: `https://yeopgang-backend.onrender.com`)

### 환경 변수 설정

Render 대시보드의 각 서비스에서 다음 환경 변수를 설정하세요:

#### 백엔드 서비스

| 변수명 | 값 | 설명 |
|--------|-----|------|
| `OPENAI_API_KEY` | `your_key` | OpenAI API 키 (필수) |
| `DATABASE_URL` | `sqlite:///./data/yeopgang.db` | 데이터베이스 URL |
| `DATA_ROOT` | `data` | 데이터 루트 디렉토리 |
| `CHROMA_DB_PATH` | `data/chroma` | ChromaDB 경로 |
| `LLM_MODEL` | `gpt-4o-mini` | LLM 모델 (선택사항) |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | 임베딩 모델 (선택사항) |

#### 프론트엔드 서비스

| 변수명 | 값 | 설명 |
|--------|-----|------|
| `NEXT_PUBLIC_API_URL` | `https://yeopgang-backend.onrender.com` | 백엔드 API URL |

### 중요 사항

1. **영구 디스크 (Persistent Disk)**

   SQLite 데이터베이스와 업로드된 파일을 저장하기 위해 Render의 영구 디스크를 사용해야 합니다. 백엔드 서비스에 디스크를 추가하고 `/app/data` 경로에 마운트하세요.

2. **서비스 URL**

   프론트엔드의 `NEXT_PUBLIC_API_URL`은 백엔드 서비스의 실제 URL로 설정해야 합니다. Render는 각 서비스에 고유한 URL을 제공합니다.

3. **무료 플랜 제한사항**

   - Render 무료 플랜은 서비스가 15분간 비활성 상태일 때 자동으로 슬리프 모드로 전환됩니다.
   - 첫 요청 시 깨우는 데 시간이 걸릴 수 있습니다.
   - 월간 사용 시간 제한이 있습니다.

4. **CORS 설정**

   백엔드의 CORS 설정이 프론트엔드 도메인을 허용하도록 확인하세요. 현재 설정은 모든 도메인을 허용하므로 문제없습니다.

## 🔧 문제 해결

### Docker 로컬 실행 문제

**포트가 이미 사용 중인 경우:**

```bash
# 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# docker-compose.yml에서 포트 변경
```

**볼륨 마운트 오류:**

Windows에서 경로 문제가 발생할 수 있습니다. `docker-compose.yml`의 볼륨 경로를 절대 경로로 변경하세요.

### Render 배포 문제

**빌드 실패:**

- Dockerfile 경로와 컨텍스트가 올바른지 확인
- 환경 변수가 모두 설정되었는지 확인
- Render 로그에서 오류 메시지 확인

**서비스 간 연결 문제:**

- 프론트엔드의 `NEXT_PUBLIC_API_URL`이 올바른지 확인
- 백엔드 서비스가 실행 중인지 확인
- CORS 설정 확인

**데이터베이스 문제:**

- 영구 디스크가 올바르게 마운트되었는지 확인
- 디스크 용량이 충분한지 확인

**서비스가 자주 재시작되는 경우:**

- 로그에서 오류 확인
- 메모리 사용량 확인
- 환경 변수 설정 확인

## 📚 추가 리소스

- [Render 공식 문서](https://render.com/docs)
- [Docker 공식 문서](https://docs.docker.com/)
- [Next.js 배포 가이드](https://nextjs.org/docs/deployment)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
