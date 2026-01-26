# ==================== Server Dockerfile ====================
# 백엔드 서버만 배포하는 Dockerfile
FROM python:3.11-slim-bookworm

WORKDIR /app

# 시스템 의존성 설치 (ffmpeg for Whisper STT)
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel build && \
    pip install --no-cache-dir -r requirements.txt

# Server 코드 복사
COPY . .

# 데이터 디렉토리 생성
RUN mkdir -p data/uploads data/chroma && \
    chmod -R 755 data

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
