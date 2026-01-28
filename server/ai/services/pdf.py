"""
PDF 처리 서비스: 텍스트 추출 및 이미지(도표/그림) 설명 생성
"""
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import io
import base64
import hashlib
import time
import sys
from collections import OrderedDict

from ai.config import AISettings

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

# 이미지 설명 캐시 (API 비용 절감용)
_IMAGE_DESC_CACHE: "OrderedDict[str, Tuple[float, str]]" = OrderedDict()
_IMAGE_DESC_CACHE_TTL_SECONDS = 3600
_IMAGE_DESC_CACHE_MAX = 512
_MAX_IMAGES_PER_PAGE = 6
_MAX_IMAGES_TOTAL = 50


# MuPDF 에러 메시지 필터링을 위한 stderr 래퍼
class MuPDFErrorFilter:
    """MuPDF 에러 메시지를 필터링하는 stderr 래퍼"""
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
    
    def write(self, text):
        # MuPDF 관련 에러 메시지 필터링
        if "MuPDF error" in text or "syntax error: invalid key in dict" in text:
            return  # 무시
        self.original_stderr.write(text)
    
    def flush(self):
        self.original_stderr.flush()


def _image_cache_get(key: str) -> Optional[str]:
    cached = _IMAGE_DESC_CACHE.get(key)
    if not cached:
        return None
    cached_at, cached_text = cached
    if time.time() - cached_at > _IMAGE_DESC_CACHE_TTL_SECONDS:
        _IMAGE_DESC_CACHE.pop(key, None)
        return None
    _IMAGE_DESC_CACHE.move_to_end(key)
    return cached_text


def _image_cache_set(key: str, value: str) -> None:
    _IMAGE_DESC_CACHE[key] = (time.time(), value)
    _IMAGE_DESC_CACHE.move_to_end(key)
    if len(_IMAGE_DESC_CACHE) > _IMAGE_DESC_CACHE_MAX:
        _IMAGE_DESC_CACHE.popitem(last=False)


def _openai_client(settings: AISettings):
    """OpenAI 클라이언트 생성 (Vision API용)"""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=settings.openai_api_key)


def describe_image_with_vision(
    image_bytes: bytes, 
    settings: AISettings,
    page_num: int,
    context: Optional[str] = None
) -> str:
    """
    OpenAI Vision API를 사용하여 이미지(도표/그림) 설명 생성
    
    Args:
        image_bytes: 이미지 바이트 데이터
        settings: AISettings 인스턴스
        page_num: PDF 페이지 번호 (컨텍스트용)
        context: 이미지 주변 텍스트 (선택적)
    
    Returns:
        이미지에 대한 설명 텍스트
    """
    if OpenAI is None or not settings.openai_api_key:
        print(f"Warning: OPENAI_API_KEY is not set. Cannot describe image for page {page_num}.")
        return f"이미지 설명 플레이스홀더 (페이지 {page_num}). OPENAI_API_KEY가 설정되지 않았습니다."

    # 캐시 확인 (이미지 바이트 기반)
    image_hash = hashlib.md5(image_bytes).hexdigest()
    cached = _image_cache_get(image_hash)
    if cached:
        return cached

    client = _openai_client(settings)
    
    # 이미지 바이트를 base64로 인코딩
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = (
        f"이 이미지는 강의 자료의 PDF에서 추출된 도표, 그래프, 그림, 다이어그램, 또는 텍스트가 포함된 이미지입니다. "
        f"이미지의 모든 요소를 자세히 분석하고 설명해주세요.\n\n"
        f"**절대 지켜야 할 규칙 - 숫자·기호 절대 누락 금지**:\n"
        f"- 이미지에 보이는 모든 숫자(0-9)를 하나도 빠뜨리지 말고 정확히 읽어주세요.\n"
        f"- 수식이나 공식에 있는 모든 숫자, 계수, 상수를 정확히 기록하세요. 예: '2x'에서 2를 빼먹으면 안 됩니다.\n"
        f"- 모든 수학 기호(+, -, ×, ÷, =, <, >, ≤, ≥, ≠, √, ^, 등)를 정확히 읽어주세요.\n"
        f"- 변수나 문자(x, y, z, a, b, c 등)도 모두 읽어주세요.\n"
        f"- 지수나 제곱 표시(예: x², y³)도 정확히 읽어주세요.\n"
        f"- 분수나 비율 표시도 정확히 읽어주세요 (예: 1/2, 3/4).\n"
        f"- 레이블, 축 이름, 범례의 모든 텍스트와 숫자를 읽어주세요.\n"
        f"- 추상적인 요약보다는, 보이는 숫자와 기호를 그대로 정확히 기술하는 것이 중요합니다.\n\n"
        f"**설명 항목**:\n"
        f"- 도형/그래프인 경우: 모양, 선분, 각도, 좌표, 수식, 레이블, 축, 데이터 값, 범례 등\n"
        f"- 그림/다이어그램인 경우: 요소들 간의 관계, 주요 특징, 구조, 흐름 등\n"
        f"- 텍스트가 포함된 경우: 모든 텍스트 내용, 수식, 기호, 레이블을 하나도 빠뜨리지 말고 읽어주세요\n\n"
        f"한국어로 상세하고 정확하게 설명해주세요. 특히 숫자와 기호는 절대 누락하지 마세요."
    )
    
    if context:
        prompt += f"\n\n참고: 이 이미지 주변의 텍스트 컨텍스트:\n{context[:500]}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Vision API 지원 모델
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )
        result_text = response.choices[0].message.content
        
        # 응답 검증: 이상한 응답이 오면 재시도
        if result_text and ("죄송하지만" in result_text or "직접 분석" in result_text or "불가능합니다" in result_text or "식별하는 것은 불가능" in result_text):
            print(f"⚠️ Vision API 응답이 이상합니다. 재시도 중... (페이지 {page_num})")
            # 프롬프트를 더 명확하게 수정하여 재시도
            retry_prompt = (
                f"이 이미지는 강의 자료의 PDF에서 추출된 도표, 그래프, 그림, 다이어그램, 또는 텍스트가 포함된 이미지입니다. "
                f"이미지의 모든 요소를 자세히 분석하고 설명해주세요.\n\n"
                f"**절대 지켜야 할 규칙 - 숫자·기호 절대 누락 금지**:\n"
                f"- 이미지에 보이는 모든 숫자(0-9)를 하나도 빠뜨리지 말고 정확히 읽어주세요.\n"
                f"- 수식이나 공식에 있는 모든 숫자, 계수, 상수를 정확히 기록하세요. 예: '2x'에서 2를 빼먹으면 안 됩니다.\n"
                f"- 모든 수학 기호(+, -, ×, ÷, =, <, >, ≤, ≥, ≠, √, ^, 등)를 정확히 읽어주세요.\n"
                f"- 변수나 문자(x, y, z, a, b, c 등)도 모두 읽어주세요.\n"
                f"- 지수나 제곱 표시(예: x², y³)도 정확히 읽어주세요.\n"
                f"- 분수나 비율 표시도 정확히 읽어주세요 (예: 1/2, 3/4).\n"
                f"- 레이블, 축 이름, 범례의 모든 텍스트와 숫자를 읽어주세요.\n"
                f"- 추상적인 요약보다는, 보이는 숫자와 기호를 그대로 정확히 기술하는 것이 중요합니다.\n\n"
                f"**설명 항목**:\n"
                f"- 도형/그래프인 경우: 모양, 선분, 각도, 좌표, 수식, 레이블, 축, 데이터 값, 범례 등\n"
                f"- 그림/다이어그램인 경우: 요소들 간의 관계, 주요 특징, 구조, 흐름 등\n"
                f"- 텍스트가 포함된 경우: 모든 텍스트 내용, 수식, 기호, 레이블을 하나도 빠뜨리지 말고 읽어주세요\n\n"
                f"이미지를 직접 보고 분석하여 상세히 설명해주세요. 특히 숫자와 기호는 절대 누락하지 마세요."
            )
            if context:
                retry_prompt += f"\n\n참고 컨텍스트: {context[:500]}"
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": retry_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                            ],
                        }
                    ],
                    max_tokens=1000,
                )
                result_text = response.choices[0].message.content
            except Exception as retry_error:
                print(f"⚠️ Vision API 재시도 실패 (페이지 {page_num}): {retry_error}")
        
        if result_text:
            _image_cache_set(image_hash, result_text)
        return result_text or f"이미지 설명 생성 실패 (페이지 {page_num})"
    except Exception as e:
        print(f"Error describing image with Vision API (page {page_num}): {e}")
        return f"이미지 설명 생성 오류 (페이지 {page_num}): {str(e)}"


def extract_pdf_content(
    pdf_path: str, 
    settings: AISettings, 
    extract_images: bool = False
) -> Dict[str, List[Any]]:
    """
    PDF 파일에서 텍스트를 추출하고, 선택적으로 이미지 설명을 생성합니다.
    각 페이지의 텍스트와 메타데이터를 반환합니다.
    """
    if fitz is None:
        raise ImportError(
            "PyMuPDF (fitz) is required for PDF processing. Install with: pip install pymupdf"
        )
    if extract_images and (Image is None or OpenAI is None or not settings.openai_api_key):
        print("Warning: Pillow or OpenAI not installed/configured. Image extraction/description will be skipped.")
        extract_images = False # 이미지 추출 비활성화

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    
    doc = fitz.open(path)
    all_texts: List[str] = []
    all_metadata: List[Dict[str, Any]] = []
    
    # MuPDF 에러 필터링 활성화
    original_stderr = sys.stderr
    sys.stderr = MuPDFErrorFilter(original_stderr)
    
    try:
        total_image_count = 0
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                
                # 1. 텍스트 추출 (오류 발생 시 빈 문자열로 처리)
                try:
                    page_text = page.get_text("text").strip()
                except Exception as e:
                    print(f"⚠️ 텍스트 추출 오류 (페이지 {page_num + 1}): {e}")
                    page_text = ""  # 텍스트 추출 실패 시 빈 문자열
                
                # 2. 이미지 추출 (선택적)
                image_descriptions: List[str] = []
                if extract_images:
                    try:
                        image_list = page.get_images(full=True)
                        print(f"📄 페이지 {page_num + 1}: 이미지 {len(image_list)}개 발견")
                        if len(image_list) > _MAX_IMAGES_PER_PAGE:
                            print(f"⚠️ 페이지 {page_num + 1}: 이미지 {len(image_list)}개 중 {_MAX_IMAGES_PER_PAGE}개만 처리")
                            image_list = image_list[:_MAX_IMAGES_PER_PAGE]
                    except Exception as e:
                        print(f"⚠️ 이미지 목록 추출 오류 (페이지 {page_num + 1}): {e}")
                        image_list = []  # 이미지 목록 추출 실패 시 빈 리스트
                    
                    # 이미지 주변 텍스트를 컨텍스트로 사용
                    context_text = page_text[:1000] if page_text else ""  # 간단한 컨텍스트
                    
                    if len(image_list) == 0:
                        print(f"📄 페이지 {page_num + 1}: 이미지가 없습니다.")
                    
                    for img_idx, img_info in enumerate(image_list):
                        if total_image_count >= _MAX_IMAGES_TOTAL:
                            print(f"⚠️ 이미지 설명 최대치({_MAX_IMAGES_TOTAL}) 도달, 이후 이미지 처리 생략")
                            break
                        try:
                            xref = img_info[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            # 이미지 설명 생성
                            print(f"🖼️ 이미지 설명 생성 중 (페이지 {page_num + 1}, 이미지 {img_idx + 1})...")
                            description = describe_image_with_vision(
                                image_bytes=image_bytes,
                                settings=settings,
                                page_num=page_num + 1,  # 1-based 페이지 번호
                                context=context_text,
                            )
                            image_descriptions.append(f"이미지/도표 설명 (페이지 {page_num + 1}-{img_idx + 1}): {description}")
                            print(f"✅ 이미지 설명 생성 완료 (페이지 {page_num + 1}, 이미지 {img_idx + 1}): {description[:100]}...")
                            total_image_count += 1
                            
                        except Exception as e:
                            print(f"⚠️ 이미지 추출 오류 (페이지 {page_num + 1}, 이미지 {img_idx + 1}): {e}")
                            continue  # 개별 이미지 오류는 건너뛰고 계속 진행
                
                # 3. 텍스트와 이미지 설명을 결합
                combined_text = page_text
                if image_descriptions:
                    combined_text += "\n\n" + "\n\n".join(image_descriptions)
                    print(f"📄 페이지 {page_num + 1}: 이미지 설명 {len(image_descriptions)}개 추가됨")
                else:
                    if extract_images:
                        print(f"📄 페이지 {page_num + 1}: 이미지 설명 없음 (이미지가 없거나 추출 실패)")
                
                if combined_text.strip():  # 내용이 있는 경우만 추가
                    all_texts.append(combined_text)
                    all_metadata.append({
                        "source": path.name,
                        "page_number": page_num + 1,  # 1-based
                        "type": "pdf_page",
                    })
                elif page_text.strip():  # 텍스트만 있어도 추가
                    all_texts.append(page_text)
                    all_metadata.append({
                        "source": path.name,
                        "page_number": page_num + 1,
                        "type": "pdf_page",
                    })
            except Exception as e:
                # 페이지 전체 처리 실패 시에도 계속 진행
                print(f"⚠️ 페이지 {page_num + 1} 처리 오류: {e}")
                print(f"⚠️ 해당 페이지를 건너뛰고 계속 진행합니다.")
                continue  # 다음 페이지로 계속 진행
        
        return {
            "texts": all_texts,
            "metadata": all_metadata,
        }
        
    finally:
        # 원래 stderr 복원
        sys.stderr = original_stderr
        doc.close()

