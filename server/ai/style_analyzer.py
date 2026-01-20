"""
Style Analyzer Module
강사 스타일 자동 분석 및 동적 프롬프트 생성

- 영상이 업로드되고 STT가 완료되면, 스크립트 초반 5분 분량을 분석
- 출력값: tone(말투), philosophy(교육 철학), signature_keywords(자주 쓰는 말)를 담은 JSON
"""
from typing import Dict, List, Any, Optional
import json

from ai.config import AISettings

try:
    from openai import OpenAI
    from openai import RateLimitError, APIError
except Exception:
    OpenAI = None  # type: ignore
    RateLimitError = None  # type: ignore
    APIError = None  # type: ignore


def extract_first_5_minutes(segments: List[Dict[str, Any]]) -> str:
    """
    세그먼트에서 초반 5분(300초) 분량의 텍스트 추출
    
    Args:
        segments: transcript segments (start, end, text 포함)
        
    Returns:
        초반 5분 분량의 텍스트
    """
    if not segments:
        return ""
    
    five_minutes = 300.0  # 5분 = 300초
    text_parts = []
    
    for seg in segments:
        start_time = seg.get("start", 0.0)
        
        # 5분 이내 세그먼트만 포함
        if start_time <= five_minutes:
            text = seg.get("text", "").strip()
            if text:
                text_parts.append(text)
        else:
            # 5분을 초과하면 중단
            break
    
    return " ".join(text_parts)


def analyze_instructor_style(
    segments: List[Dict[str, Any]],
    settings: Optional[AISettings] = None
) -> Dict[str, Any]:
    """
    강사 스타일 분석 (초반 5분 분량)
    
    Args:
        segments: transcript segments
        settings: AISettings 인스턴스
        
    Returns:
        {
            "tone": "말투 특징",
            "philosophy": "교육 철학 (암기 vs 이해)",
            "signature_keywords": ["자주 쓰는 말1", "자주 쓰는 말2", ...]
        }
    """
    settings = settings or AISettings()
    
    # 초반 5분 분량 추출
    sample_text = extract_first_5_minutes(segments)
    
    if not sample_text or len(sample_text.strip()) < 100:
        # 샘플이 너무 짧으면 fallback
        return {
            "tone": "정중하고 친근한 말투",
            "philosophy": "이해 중심 교육",
            "signature_keywords": []
        }
    
    if OpenAI is None or not settings.openai_api_key:
        # API 키가 없으면 기본값 반환
        print("⚠️ OPENAI_API_KEY가 없어 Style Analyzer를 건너뜁니다.")
        return {
            "tone": "정중하고 친근한 말투",
            "philosophy": "이해 중심 교육",
            "signature_keywords": []
        }
    
    client = OpenAI(api_key=settings.openai_api_key)
    
    # LLM 프롬프트 구성
    analysis_prompt = f"""다음은 강사의 강의 초반 5분 분량 텍스트입니다. 이 강사의 말투, 교육 철학, 자주 사용하는 표현을 분석해주세요.

강의 샘플 (초반 5분):
{sample_text[:3000]}  # 최대 3000자

분석할 요소:
1. **tone (말투)**: 종결어미 패턴, 어투 (정중함/친근함/격식/캐주얼), 문장 구조 특징
2. **philosophy (교육 철학)**: 암기 중심 vs 이해 중심, 설명 방식 (예시 위주/이론 위주), 학습자에 대한 접근법
3. **signature_keywords (자주 쓰는 말)**: 반복적으로 사용하는 고유 표현, 습관적 말투, 특징적인 단어나 구문 (최대 5개)

다음 JSON 형식으로 정확히 응답해주세요:
{{
    "tone": "말투 특징을 1-2문장으로 설명",
    "philosophy": "교육 철학을 1-2문장으로 설명 (암기 vs 이해 중심, 설명 방식 등)",
    "signature_keywords": ["자주 쓰는 말1", "자주 쓰는 말2", ...]
}}"""

    try:
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 언어학자이자 교육학자입니다. 주어진 텍스트에서 강사의 말투, 교육 철학, 특징적인 표현을 정확하게 분석합니다. 반드시 유효한 JSON 형식으로만 응답합니다.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},  # JSON 형식 강제
        )
        
        response_text = resp.choices[0].message.content
        
        # JSON 파싱
        try:
            persona_profile = json.loads(response_text)
            
            # 필수 필드 확인 및 기본값 설정
            result = {
                "tone": persona_profile.get("tone", "정중하고 친근한 말투"),
                "philosophy": persona_profile.get("philosophy", "이해 중심 교육"),
                "signature_keywords": persona_profile.get("signature_keywords", []) or []
            }
            
            # signature_keywords가 문자열 리스트인지 확인
            if not isinstance(result["signature_keywords"], list):
                result["signature_keywords"] = []
            
            # 최대 5개로 제한
            result["signature_keywords"] = result["signature_keywords"][:5]
            
            print(f"[Style Analyzer] ✅ 분석 완료:")
            print(f"  - Tone: {result['tone'][:50]}...")
            print(f"  - Philosophy: {result['philosophy'][:50]}...")
            print(f"  - Keywords: {result['signature_keywords']}")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"[Style Analyzer] ⚠️ JSON 파싱 오류: {e}")
            print(f"[Style Analyzer] 응답 텍스트: {response_text[:200]}")
            # JSON 파싱 실패 시 기본값 반환
            return {
                "tone": "정중하고 친근한 말투",
                "philosophy": "이해 중심 교육",
                "signature_keywords": []
            }
            
    except (RateLimitError, APIError) as e:
        error_msg = f"OpenAI API 오류 (Style Analyzer): {str(e)}"
        print(f"[Style Analyzer] ❌ {error_msg}")
        # API 오류 시 기본값 반환
        return {
            "tone": "정중하고 친근한 말투",
            "philosophy": "이해 중심 교육",
            "signature_keywords": []
        }
    except Exception as e:
        error_msg = f"Style Analyzer 오류: {str(e)}"
        print(f"[Style Analyzer] ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        # 오류 시 기본값 반환
        return {
            "tone": "정중하고 친근한 말투",
            "philosophy": "이해 중심 교육",
            "signature_keywords": []
        }


def create_persona_prompt(persona_profile: Dict[str, Any]) -> str:
    """
    persona_profile을 기반으로 시스템 프롬프트 생성
    
    Args:
        persona_profile: {
            "tone": "...",
            "philosophy": "...",
            "signature_keywords": [...]
        }
        
    Returns:
        페르소나 프롬프트 문자열
    """
    tone = persona_profile.get("tone", "정중하고 친근한 말투")
    philosophy = persona_profile.get("philosophy", "이해 중심 교육")
    keywords = persona_profile.get("signature_keywords", [])
    
    keywords_text = ""
    if keywords:
        keywords_list = ", ".join(f'"{kw}"' for kw in keywords)
        keywords_text = f"\n- 자주 사용하는 표현: {keywords_list} (이 표현들을 자연스럽게 답변에 포함하세요)"
    
    persona_prompt = f"""당신은 이 강의를 가르치는 강사입니다. 다음 분석된 특징을 정확히 반영하여 답변하세요:

**말투 (Tone):**
{tone}

**교육 철학 (Philosophy):**
{philosophy}

**특징:**
- 위 말투와 철학을 일관되게 유지하세요
- 학생에게 직접적으로 설명하는 톤으로 답변하세요 ('여러분', '학생들' 같은 표현 대신 '저는', '제가' 사용){keywords_text}

위 특징을 반영하여 자연스럽고 일관된 말투로 답변하세요."""
    
    return persona_prompt

