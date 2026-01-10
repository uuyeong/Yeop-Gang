import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env early so env vars are present when this module is imported
try:
    project_root = Path(__file__).resolve().parents[2]
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path)
except Exception:
    # If .env is missing or unreadable, continue; os.environ may already have values
    pass


@dataclass
class AISettings:
    """AI-related environment configuration."""

    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_credentials_path: Optional[str] = None  # Google 서비스 계정 키 파일 경로
    chroma_db_path: str = "data/chroma"
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    def __post_init__(self):
        """Initialize fields from environment variables after instantiation."""
        # Ensure .env is loaded (may have been loaded earlier, but ensure it's loaded)
        try:
            project_root = Path(__file__).resolve().parents[2]
            env_path = project_root / ".env"
            print(f"[DEBUG] Loading .env from: {env_path}")
            if env_path.exists():
                print(f"[DEBUG] .env file exists: {env_path.exists()}")
                load_dotenv(dotenv_path=env_path, override=True)
                print(f"[DEBUG] .env loaded (override=True)")
            else:
                print(f"[DEBUG] ⚠️ .env file not found at: {env_path}")
        except Exception as e:
            print(f"[DEBUG] ⚠️ Error loading .env: {e}")
            pass
        
        # Read from environment (will use .env if loaded, or existing os.environ)
        # Only override if field has default value (not explicitly set)
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            if self.openai_api_key:
                # API 키의 처음 10글자만 로그에 표시 (보안)
                api_key_preview = self.openai_api_key[:10] + "..." + self.openai_api_key[-4:] if len(self.openai_api_key) > 14 else "***"
                print(f"[DEBUG] ✅ OPENAI_API_KEY loaded: {api_key_preview} (length: {len(self.openai_api_key)})")
            else:
                print(f"[DEBUG] ⚠️ OPENAI_API_KEY is None or empty!")
                # os.environ에서 직접 확인
                env_key = os.environ.get("OPENAI_API_KEY")
                if env_key:
                    print(f"[DEBUG] ⚠️ But os.environ has OPENAI_API_KEY: {env_key[:10]}...")
                else:
                    print(f"[DEBUG] ⚠️ os.environ also does not have OPENAI_API_KEY")
        if self.google_api_key is None:
            self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if self.google_credentials_path is None:
            self.google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if self.chroma_db_path == "data/chroma":
            self.chroma_db_path = os.getenv("CHROMA_DB_PATH", "data/chroma")
        
        # chroma_db_path를 절대 경로로 변환 (server 폴더 기준)
        if self.chroma_db_path:
            chroma_path = Path(self.chroma_db_path)
            if not chroma_path.is_absolute():
                # server/ai/config.py -> server
                server_dir = Path(__file__).resolve().parent.parent
                self.chroma_db_path = str((server_dir / self.chroma_db_path).resolve())
        
        if self.llm_model == "gpt-4o-mini":
            self.llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        if self.embedding_model == "text-embedding-3-small":
            self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

