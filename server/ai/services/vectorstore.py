from pathlib import Path
from typing import Any, Optional
import os
import sys

# ChromaDB telemetry 비활성화 (모듈 import 전에 설정)
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"

# ChromaDB 텔레메트리 관련 오류 메시지 필터링
# ChromaDB 0.5.11에서 텔레메트리 모듈의 capture() 함수 시그니처 불일치로 인한 오류 방지
class TelemetryErrorFilter:
    """ChromaDB 텔레메트리 오류 메시지를 필터링하는 stderr 래퍼"""
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
    
    def write(self, text):
        # "Failed to send telemetry event" 또는 "capture() takes" 관련 메시지 필터링
        if "Failed to send telemetry event" in text or "capture() takes" in text:
            return  # 무시
        self.original_stderr.write(text)
    
    def flush(self):
        self.original_stderr.flush()
    
    def __getattr__(self, name):
        # 다른 속성은 원본 stderr에서 가져오기
        return getattr(self.original_stderr, name)

# stderr 필터 적용 (이미 적용되지 않은 경우에만)
if not hasattr(sys.stderr, '_is_telemetry_filtered'):
    sys.stderr = TelemetryErrorFilter(sys.stderr)
    sys.stderr._is_telemetry_filtered = True

from ai.config import AISettings


def get_chroma_client(settings: AISettings) -> "chromadb.ClientAPI":
    """Initialize or reuse a persistent Chroma client."""
    import chromadb
    import os
    
    # Lazy import to avoid native extension issues at module import time
    
    # Telemetry를 비활성화하여 "capture() takes 1 positional argument but 3 were given" 에러 방지
    # 환경 변수와 코드 설정 모두 적용
    os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
    
    Path(settings.chroma_db_path).mkdir(parents=True, exist_ok=True)
    
    # Settings 객체 생성
    chroma_settings = chromadb.Settings(
        anonymized_telemetry=False,
        allow_reset=True,
    )
    
    # stderr 필터가 이미 텔레메트리 오류를 필터링하므로 그냥 생성
    return chromadb.PersistentClient(
        path=settings.chroma_db_path,
        settings=chroma_settings
    )


def get_collection(
    client: "chromadb.ClientAPI",
    settings: AISettings,
    name: Optional[str] = None,
) -> Any:
    """
    Return a collection for course-scoped embeddings.
    Use embedding_model suffix to avoid dimension mismatch across models.
    """
    coll_name = name or f"courses-{settings.embedding_model}"
    return client.get_or_create_collection(name=coll_name)

