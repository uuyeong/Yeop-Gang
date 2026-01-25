# 배포 가이드

이 문서는 Docker와 Render를 사용한 배포 방법을 설명합니다.

## 📋 목차

1. [무료 배포 (render.yaml 없이)](#-무료-배포-renderyaml-없이)
2. [로컬 Docker 실행](#-로컬-docker-실행)
3. [Render 배포 (render.yaml 사용)](#-render-배포-renderyaml-사용)
4. [환경 변수 설정](#환경-변수-설정)
5. [문제 해결](#-문제-해결)

---

## 🆓 무료 배포 (render.yaml 없이)

**render.yaml은 필수가 아닙니다.** Render 대시보드에서 서비스를 직접 만들면 됩니다.

### 방법 1: 통합 Dockerfile 사용 (권장) ⭐

**하나의 서비스로 Client와 Server를 함께 배포합니다.**

1. [Render](https://render.com) 로그인 → **Dashboard** → **New +** → **Web Service**
2. GitHub 저장소 연결 후 이 프로젝트 선택
3. 아래처럼 설정:
   - **Name**: `yeopgang-app` (원하는 이름)
   - **Region**: Singapore (가까운 지역)
   - **Runtime**: **Docker**
   - **Dockerfile Path**: `Dockerfile` (root의 Dockerfile)
   - **Docker Context**: `.` (프로젝트 루트)
   - **Plan**: **Free**
4. **Environment** 탭에서 **Add Environment Variable**:
   - `OPENAI_API_KEY` = (본인 OpenAI 키)
   - `DATABASE_URL` = `sqlite:///./server/data/yeopgang.db`
   - `DATA_ROOT` = `server/data`
   - `CHROMA_DB_PATH` = `server/data/chroma`
   - `NEXT_PUBLIC_API_URL` = `http://localhost:8000` (또는 배포 후 실제 백엔드 URL)
5. **Create Web Service** 클릭

**장점**: 하나의 서비스로 관리, 간단함  
**단점**: 두 서비스가 하나의 컨테이너에서 실행 (무료 플랜에서는 문제없음)

### 방법 2: 분리된 Dockerfile 사용 (기존 방식)

**Client와 Server를 별도 서비스로 배포합니다.**

#### 1. 백엔드 배포

1. [Render](https://render.com) 로그인 → **Dashboard** → **New +** → **Web Service**
2. GitHub 저장소 연결 후 이 프로젝트 선택
3. 아래처럼 설정:
   - **Name**: `yeopgang-backend` (원하는 이름)
   - **Region**: Singapore (가까운 지역)
   - **Runtime**: **Docker**
   - **Dockerfile Path**: `server/Dockerfile`
   - **Docker Context**: `server`
   - **Plan**: **Free**
4. **Environment** 탭에서 **Add Environment Variable**:
   - `OPENAI_API_KEY` = (본인 OpenAI 키)
   - `DATABASE_URL` = `sqlite:///./data/yeopgang.db`
   - `DATA_ROOT` = `data`
   - `CHROMA_DB_PATH` = `data/chroma`
5. **Create Web Service** 클릭

배포가 끝나면 **URL**이 나옵니다. 예: `https://yeopgang-backend.onrender.com` → **복사해 두기.**

#### 2. 프론트엔드 배포

1. **New +** → **Web Service** → 같은 저장소 선택
2. 설정:
   - **Name**: `yeopgang-frontend`
   - **Runtime**: **Docker**
   - **Dockerfile Path**: `client/Dockerfile`
   - **Docker Context**: `client`
   - **Plan**: **Free**
3. **Environment**:
   - `NEXT_PUBLIC_API_URL` = `https://yeopgang-backend.onrender.com`  
     (위에서 복사한 백엔드 URL로 **반드시** 변경)
4. **Create Web Service** 클릭

### 3. 무료 플랜 안내

| 항목 | 내용 |
|------|------|
| **비용** | 0원 (Render Free) |
| **슬립** | 15분 미사용 시 슬립 → 첫 요청 시 30초~1분 정도 깨우는 시간 |
| **디스크** | **영구 디스크 없음.** SQLite DB·업로드 파일은 **재배포/재시작 시 사라집니다.** |
| **용도** | 데모·테스트용으로 적합. 실제 서비스·데이터 보존이 필요하면 **Starter 유료 + 디스크** 필요 |

데이터를 남기고 싶다면 [Render 플랜](https://render.com/pricing)에서 **Starter** 이상 + **Persistent Disk** 연결이 필요합니다.  
**render.yaml**은 나중에 Blueprint로 한 번에 배포하고 싶을 때만 쓰면 됩니다.

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

2. **Docker Compose로 실행** (통합 Dockerfile 사용)

   ```bash
   docker-compose up --build
   ```

   또는 백그라운드에서 실행:

   ```bash
   docker-compose up -d --build
   ```

   **또는 직접 Docker로 실행:**

   ```bash
   docker build -t yeopgang-app --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 .
   docker run -p 3000:3000 -p 8000:8000 \
     -e OPENAI_API_KEY=your_key \
     -e DATABASE_URL=sqlite:///./server/data/yeopgang.db \
     -v $(pwd)/server/data:/app/server/data \
     yeopgang-app
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

## ☁️ Render 배포 (render.yaml 사용)

**render.yaml 없이** 무료 배포하려면 위 [무료 배포 (render.yaml 없이)](#-무료-배포-renderyaml-없이) 섹션을 따르면 됩니다.

아래는 **Blueprint**(render.yaml)로 한 번에 배포하는 방법입니다.

### 사전 준비

1. [Render](https://render.com) 계정 생성
2. GitHub 저장소 연결 (또는 GitLab, Bitbucket)

### 배포 단계 (Blueprint)

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

> **참고**: render.yaml의 `disk` 설정은 **유료 플랜(Starter 이상)**에서만 동작합니다. 무료는 디스크 없이 배포됩니다.

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

1. **서비스 URL**

   프론트엔드의 `NEXT_PUBLIC_API_URL`은 백엔드 서비스의 **실제 URL**로 설정해야 합니다. 예: `https://yeopgang-backend.onrender.com`

2. **무료 플랜 제한사항**

   - 15분 미사용 시 슬립 → 첫 요청 시 30초~1분 정도 깨우는 시간
   - **영구 디스크 없음** → DB·업로드 파일은 재배포/재시작 시 삭제됨 (데모용 적합)
   - 월간 사용 시간 제한 있음

3. **영구 디스크 (유료 플랜)**

   데이터를 유지하려면 **Starter 이상** + Persistent Disk (`/app/data`) 연결이 필요합니다. render.yaml 없이 수동 배포 시에도 서비스 설정에서 디스크를 추가할 수 있습니다.

4. **CORS**

   현재 백엔드는 모든 도메인 허용이므로 별도 설정 없이 사용 가능합니다.

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
