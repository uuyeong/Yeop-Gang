# ==================== Client 빌드 스테이지 ====================
FROM node:20-alpine AS client-builder

WORKDIR /app/client

# Client 의존성 설치 (캐시 최적화: package.json이 변경되지 않으면 이 레이어 재사용)
COPY client/package*.json ./
RUN npm ci --prefer-offline --no-audit

# Client 소스 코드 복사 및 빌드 (소스 코드만 변경되면 이 레이어부터 재빌드)
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
# 캐시 최적화: 시스템 패키지는 거의 변경되지 않으므로 별도 레이어로 분리
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 빌드 도구 설치 (의존성과 분리하여 캐싱 최적화)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel build

# Python 의존성 설치 (requirements.txt가 변경되지 않으면 이 레이어 재사용)
COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ==================== 최종 실행 스테이지 ====================
FROM python:3.11-slim-bookworm

# 시스템 의존성 설치 (캐시 최적화: 시스템 패키지는 거의 변경되지 않음)
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
# PORT는 Render가 동적으로 할당하므로 기본값만 설정
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 포트 노출
# Render는 PORT 환경 변수를 제공하므로 동적으로 할당됨
# EXPOSE는 문서화 목적이며, 실제 포트는 Render가 결정
EXPOSE 3000

# 헬스체크 (프론트엔드만 확인, 백엔드는 내부에서만 접근 가능)
# Render의 PORT 환경 변수를 사용 (없으면 기본값 3000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${PORT:-3000} || exit 1'

# 시작 스크립트 실행
CMD ["/app/start.sh"]
