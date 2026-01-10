from typing import Iterable, List

from ai.config import AISettings

try:
    from openai import OpenAI
    from openai import RateLimitError, APIError
except Exception:
    OpenAI = None  # type: ignore
    RateLimitError = None  # type: ignore
    APIError = None  # type: ignore


def embed_texts(texts: Iterable[str], settings: AISettings) -> List[List[float]]:
    """
    Generate embeddings via OpenAI embeddings API.
    
    Raises:
        RuntimeError: If OpenAI client is not available or API key is missing
        ValueError: If API quota is exceeded or other API errors occur
    """
    if OpenAI is None or not settings.openai_api_key:
        raise RuntimeError("OpenAI client not available or API key is missing")
    
    # 디버깅: 실제 사용되는 API 키 확인 (너무 자주 출력하지 않도록 간소화)
    api_key_preview = settings.openai_api_key[:10] + "..." + settings.openai_api_key[-4:] if len(settings.openai_api_key) > 14 else "***"
    
    client = OpenAI(api_key=settings.openai_api_key)
    
    try:
        # OpenAI embeddings API supports batching; send as one request
        print(f"[DEBUG] [Embeddings] Creating embeddings for {len(texts)} text(s) (API key: {api_key_preview})")
        resp = client.embeddings.create(
            input=list(texts),
            model=settings.embedding_model,
        )
        print(f"[DEBUG] [Embeddings] ✅ Successfully created {len(resp.data)} embeddings")
        return [item.embedding for item in resp.data]
    except RateLimitError as e:
        # 더 상세한 에러 정보 출력
        status_code = e.status_code if hasattr(e, 'status_code') else '429'
        error_body = e.response.json() if hasattr(e, 'response') and hasattr(e.response, 'json') else {}
        error_type = error_body.get('error', {}).get('type', 'unknown')
        error_message = error_body.get('error', {}).get('message', str(e))
        
        error_msg = (
            "OpenAI API 할당량을 초과했습니다. "
            "계정의 결제 정보와 사용 한도를 확인해주세요. "
            f"에러 코드: {status_code}"
        )
        print(f"ERROR [Embeddings]: {error_msg}")
        print(f"[DEBUG] [Embeddings] RateLimitError details:")
        print(f"  - Status code: {status_code}")
        print(f"  - Error type: {error_type}")
        print(f"  - Error message: {error_message}")
        print(f"  - Using API key: {api_key_preview}")
        raise ValueError(error_msg) from e
    except APIError as e:
        error_msg = f"OpenAI API 오류가 발생했습니다: {str(e)}"
        print(f"ERROR [Embeddings]: {error_msg}")
        raise ValueError(error_msg) from e

