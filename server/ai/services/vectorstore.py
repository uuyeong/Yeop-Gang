from pathlib import Path
from typing import Any, Optional
import os

# ChromaDB telemetry 비활성화 (모듈 import 전에 설정)
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"

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

