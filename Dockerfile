# ==================== Client 빌드 스테이지 ====================
FROM node:20-alpine AS client-builder

WORKDIR /app/client

# Client 의존성 설치
COPY client/package*.json ./
RUN npm ci

# Client 빌드
COPY client/ .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
# public 디렉토리가 없으면 빈 디렉토리 생성 (standalone 빌드를 위해)
RUN mkdir -p public || true
RUN npm run build

# ==================== Server 빌드 스테이지 ====================
# bookworm(Debian 12) 사용: trixie는 security 저장소 미제공으로 404 발생
FROM python:3.11-slim-bookworm AS server-builder

WORKDIR /app/server

# 시스템 의존성 설치 (ffmpeg for Whisper STT)
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY server/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel build && \
    pip install --no-cache-dir -r requirements.txt

# ==================== 최종 실행 스테이지 ====================
FROM python:3.11-slim-bookworm

# 시스템 의존성 설치
# Node.js는 NodeSource에서 설치, ffmpeg는 Debian 저장소에서 설치
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    curl \
    bash \
    ca-certificates \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends --fix-missing nodejs \
    && apt-get install -y --no-install-recommends --fix-missing ffmpeg \
    || (apt-get update && apt-get install -y --no-install-recommends --fix-missing ffmpeg) \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Server 코드 및 의존성 복사
COPY --from=server-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=server-builder /usr/local/bin /usr/local/bin
COPY server/ ./server/

# Client 빌드 결과 복사 (standalone 출력)
COPY --from=client-builder /app/client/.next/standalone ./client/
COPY --from=client-builder /app/client/.next/static ./client/.next/static
# public 디렉토리 복사 (빈 디렉토리라도 존재하므로 안전하게 복사 가능)
COPY --from=client-builder /app/client/public ./client/public

# 데이터 디렉토리 생성
RUN mkdir -p server/data/uploads server/data/chroma && \
    chmod -R 755 server/data

# 시작 스크립트 복사
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 포트 노출
EXPOSE 3000 8000

# 헬스체크 (백엔드와 프론트엔드 모두 확인)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health && curl -f http://localhost:3000 || exit 1

# 시작 스크립트 실행
CMD ["/app/start.sh"]
