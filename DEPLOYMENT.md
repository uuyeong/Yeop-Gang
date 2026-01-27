# 배포 가이드

이 문서는 Docker와 Render를 사용한 **통합 배포** 방법을 설명합니다.

> **도메인 주소**: `https://yeop-gang.onrender.com`

## 📋 목차

1. [Render 배포](#-render-배포)
2. [로컬 Docker 실행](#-로컬-docker-실행)
3. [환경 변수 설정](#환경-변수-설정)
4. [문제 해결](#-문제-해결)

---

## 🆓 Render 배포

**통합 배포**: 하나의 서비스로 Client(Next.js)와 Server(FastAPI)를 함께 배포합니다.

**동작 방식**:
- Render는 프론트엔드 포트(3000)만 외부에 노출
- 브라우저 → `/api/*` → Next.js API Routes 프록시 → 내부 백엔드(`localhost:8000`)

### 배포 단계

1. [Render](https://render.com) 로그인 → **Dashboard** → **New +** → **Web Service**
2. GitHub 저장소 연결 후 이 프로젝트 선택
3. 아래처럼 설정:
   - **Name**: `yeop-gang` (이 이름이 URL에 사용됨)
   - **Region**: Singapore (가까운 지역)
   - **Runtime**: **Docker**
   - **Dockerfile Path**: `Dockerfile`
   - **Docker Context**: `.`
   - **Plan**: **Free**
4. **Environment** 탭에서 환경 변수 추가 (아래 표 참고)
5. **Create Web Service** 클릭

### 환경 변수 설정

| 변수명 | 값 | 설명 | 필수 |
|--------|-----|------|------|
| `OPENAI_API_KEY` | `your_openai_api_key` | OpenAI API 키 | ✅ 필수 |
| `DATABASE_URL` | `sqlite:///./server/data/yeopgang.db` | SQLite 데이터베이스 경로 | ✅ 필수 |
| `DATA_ROOT` | `server/data` | 데이터 파일 저장 루트 | ✅ 필수 |
| `CHROMA_DB_PATH` | `server/data/chroma` | ChromaDB 경로 | ✅ 필수 |
| `LLM_MODEL` | `gpt-4o-mini` | 사용할 LLM 모델 | ❌ |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | 임베딩 모델 | ❌ |

**Render 대시보드 환경 변수 예시:**

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
DATABASE_URL=sqlite:///./server/data/yeopgang.db
DATA_ROOT=server/data
CHROMA_DB_PATH=server/data/chroma
```

### 무료 플랜 안내

| 항목 | 내용 |
|------|------|
| **비용** | 0원 (Render Free) |
| **슬립** | 15분 미사용 시 슬립 → 첫 요청 시 30초~1분 깨우는 시간 |
| **디스크** | **영구 디스크 없음** → DB·업로드 파일은 재배포/재시작 시 삭제 |
| **용도** | 데모·테스트용 적합. 데이터 보존 필요 시 유료 플랜 필요 |

---

## 🐳 로컬 Docker 실행

### 사전 요구사항

- Docker Desktop 설치

### 실행 방법

1. **환경 변수 설정**

   ```bash
   cp .env.example .env
   # .env 파일을 편집하여 OPENAI_API_KEY 등 입력
   ```

2. **Docker로 빌드 및 실행**

   ```bash
   docker build -t yeopgang-app .
   docker run -p 3000:3000 \
     -e OPENAI_API_KEY=your_key \
     -e DATABASE_URL=sqlite:///./server/data/yeopgang.db \
     -v $(pwd)/server/data:/app/server/data \
     yeopgang-app
   ```

3. **서비스 접속**

   - 프론트엔드: http://localhost:3000
   - 백엔드 API (내부): http://localhost:8000
   - API 문서: http://localhost:8000/docs

4. **서비스 중지**

   ```bash
   docker stop $(docker ps -q --filter ancestor=yeopgang-app)
   ```

---

## 🔧 문제 해결

### Render 배포 문제

**빌드 실패:**

- 환경 변수가 모두 설정되었는지 확인
- Render 로그에서 오류 메시지 확인

**API 연결 오류:**

- 브라우저 개발자 도구에서 네트워크 요청 확인
- `/api/*` 경로가 올바르게 프록시되는지 확인

**데이터베이스 문제:**

- 무료 플랜은 영구 디스크가 없으므로 재배포 시 데이터 삭제됨
- 데이터 보존 필요 시 유료 플랜 + Persistent Disk 사용

### Docker 로컬 실행 문제

**포트가 이미 사용 중인 경우:**

```bash
# 포트 사용 중인 프로세스 확인 (Windows)
netstat -ano | findstr :3000

# 다른 포트로 실행
docker run -p 4000:3000 yeopgang-app
```

**볼륨 마운트 오류 (Windows):**

경로를 절대 경로로 변경하세요.

---

## ⚡ 빌드 시간 최적화

### Docker 레이어 캐싱

현재 Dockerfile은 레이어 캐싱을 최적화했습니다:
- 의존성 설치와 소스 코드 복사를 분리
- 소스 코드만 변경 시 의존성 레이어 재사용

### 빌드 시간 예상

- 첫 빌드: 5-10분
- 캐시 활용 시: 2-5분
- 소스 코드만 변경: 1-3분

---

## 📚 추가 리소스

- [Render 공식 문서](https://render.com/docs)
- [Docker 공식 문서](https://docs.docker.com/)
- [Next.js 배포 가이드](https://nextjs.org/docs/deployment)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
