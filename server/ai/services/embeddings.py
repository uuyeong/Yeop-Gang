from typing import Iterable, List, Dict, Tuple
from collections import OrderedDict

from ai.config import AISettings

try:
    from openai import OpenAI
    from openai import RateLimitError, APIError
except Exception:
    OpenAI = None  # type: ignore
    RateLimitError = None  # type: ignore
    APIError = None  # type: ignore


# 간단한 LRU 캐시 (API 비용 절감용)
_EMBED_CACHE: "OrderedDict[Tuple[str, str], List[float]]" = OrderedDict()
_EMBED_CACHE_MAX = 512
_EMBED_CACHE_LOG_ENABLED = True


def _cache_get(key: Tuple[str, str]) -> List[float] | None:
    if key in _EMBED_CACHE:
        _EMBED_CACHE.move_to_end(key)
        return _EMBED_CACHE[key]
    return None


def _cache_set(key: Tuple[str, str], value: List[float]) -> None:
    _EMBED_CACHE[key] = value
    _EMBED_CACHE.move_to_end(key)
    if len(_EMBED_CACHE) > _EMBED_CACHE_MAX:
        _EMBED_CACHE.popitem(last=False)


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
    
    try:
        text_list = list(texts)
        if not text_list:
            return []

        # 캐시 확인
        cached_embeddings: List[List[float] | None] = []
        cache_hit_count = 0
        missing_texts_map: Dict[str, Tuple[str, str]] = {}
        for text in text_list:
            cache_key = (settings.embedding_model, text)
            cached_value = _cache_get(cache_key)
            if cached_value is not None:
                cached_embeddings.append(cached_value)
                cache_hit_count += 1
            else:
                cached_embeddings.append(None)
                if text not in missing_texts_map:
                    missing_texts_map[text] = cache_key

        # 캐시 히트만으로 처리 가능
        if _EMBED_CACHE_LOG_ENABLED and cache_hit_count:
            print(f"[CACHE HIT] embeddings {cache_hit_count}/{len(text_list)}")

        if not missing_texts_map:
            return [emb for emb in cached_embeddings if emb is not None]

        client = OpenAI(api_key=settings.openai_api_key)
    
        # OpenAI embeddings API supports batching; send missing as one request
        missing_texts = list(missing_texts_map.keys())
        print(f"[DEBUG] [Embeddings] Creating embeddings for {len(missing_texts)} text(s) (API key: {api_key_preview})")
        resp = client.embeddings.create(
            input=missing_texts,
            model=settings.embedding_model,
        )
        print(f"[DEBUG] [Embeddings] ✅ Successfully created {len(resp.data)} embeddings")

        # 캐시 저장
        embedding_by_text: Dict[str, List[float]] = {}
        for text, item in zip(missing_texts, resp.data):
            embedding_by_text[text] = item.embedding
            _cache_set(missing_texts_map[text], item.embedding)

        # 원래 순서대로 결과 조립
        results: List[List[float]] = []
        for text, emb in zip(text_list, cached_embeddings):
            if emb is not None:
                results.append(emb)
            else:
                results.append(embedding_by_text[text])
        return results
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

