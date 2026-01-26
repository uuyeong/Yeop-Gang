# ==================== Client Dockerfile ====================
# 프론트엔드만 배포하는 Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# 의존성 설치 (캐시 최적화)
COPY package*.json ./
RUN npm ci --prefer-offline --no-audit

# 소스 코드 복사 및 빌드
COPY . .
# NEXT_PUBLIC_API_URL은 빌드 시점에 주입 (Render 환경 변수에서)
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN mkdir -p public || true
RUN npm run build

# ==================== 실행 스테이지 ====================
FROM node:20-alpine

WORKDIR /app

# 시스템 의존성 설치 (curl for healthcheck)
RUN apk add --no-cache curl

# 빌드 결과 복사
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# 환경 변수 설정
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 포트 노출
EXPOSE 3000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-3000} || exit 1

# 서버 실행
CMD ["node", "server.js"]
