"""
AI 답변 가드레일 (Guardrails)
- 윤리 가이드라인 적용
- 부적절한 콘텐츠 필터링
- 답변 품질 검증
- 프롬프트 인젝션 방어
- 부적절한 질문 필터링
"""
import re
from typing import Optional, Tuple


class Guardrails:
    """AI 답변 가드레일 클래스"""
    
    # 금지된 키워드 목록 (욕설, 위협 등)
    FORBIDDEN_KEYWORDS = [
        "폭력", "혐오", "차별", "불법", "마약", "도박",
        "시발", "개새끼", "병신", "미친", "죽어", "죽여",
        "가만있지않을거야", "가만두지않을거야", "복수", "보복",
        # 추가 금지 키워드 확장 가능
    ]
    
    # 민감한 주제 키워드
    SENSITIVE_TOPICS = [
        "정치", "종교", "성", "인종",
    ]
    
    # 프롬프트 인젝션 패턴
    PROMPT_INJECTION_PATTERNS = [
        r"지금까지의\s*프롬프트를\s*잊",
        r"이전\s*지시사항\s*무시",
        r"시스템\s*프롬프트\s*무시",
        r"당신은\s*이제",
        r"새로운\s*역할",
        r"역할\s*변경",
        r"프롬프트\s*무시",
        r"ignore\s*previous",
        r"forget\s*all",
        r"you\s*are\s*now",
        r"new\s*role",
        r"act\s*as",
        r"pretend\s*to\s*be",
    ]
    
    # 컨텍스트 외 질문 패턴 (강의와 완전히 무관한 질문만)
    # 주의: "내년 수능에 이 문제가 나올까?" 같은 질문은 강의 내용과 관련이 있으므로 허용
    OUT_OF_CONTEXT_PATTERNS = [
        r"김치찌개\s*레시피",
        r"요리\s*방법",
        r"수능\s*전체\s*예측",  # 전체 수능 예측만 차단
        r"시험\s*답안\s*알려줘",  # 답안 요청만 차단
        r"개인정보",
        r"전화번호",
        r"주소",
        r"계좌번호",
        r"비밀번호",
        r"신용카드",
    ]
    
    def __init__(self):
        self.forbidden_pattern = re.compile(
            "|".join(self.FORBIDDEN_KEYWORDS),
            re.IGNORECASE
        )
        self.prompt_injection_pattern = re.compile(
            "|".join(self.PROMPT_INJECTION_PATTERNS),
            re.IGNORECASE
        )
        self.out_of_context_pattern = re.compile(
            "|".join(self.OUT_OF_CONTEXT_PATTERNS),
            re.IGNORECASE
        )
    
    def check_content(self, text: str) -> tuple[bool, Optional[str]]:
        """
        콘텐츠 검증
        Returns: (is_safe, reason)
        """
        if not text or len(text.strip()) == 0:
            return False, "Empty content"
        
        # 금지 키워드 확인
        if self.forbidden_pattern.search(text):
            return False, "Contains forbidden keywords"
        
        # 너무 짧은 답변 (품질 검증)
        if len(text.strip()) < 10:
            return False, "Answer too short"
        
        # 너무 긴 답변 (비정상적)
        if len(text) > 10000:
            return False, "Answer too long"
        
        return True, None
    
    def filter_response(self, response: str) -> str:
        """
        응답 필터링 및 정제
        """
        # 기본 정제
        filtered = response.strip()
        
        # 연속된 공백 제거
        filtered = re.sub(r'\s+', ' ', filtered)
        
        # 금지 키워드가 포함된 경우 마스킹
        if self.forbidden_pattern.search(filtered):
            filtered = self.forbidden_pattern.sub("[필터링됨]", filtered)
        
        return filtered
    
    def validate_educational_content(self, text: str) -> tuple[bool, Optional[str]]:
        """
        교육적 콘텐츠 검증
        """
        # 교육 관련 키워드 확인 (선택적)
        educational_keywords = ["학습", "교육", "강의", "설명", "예시", "문제"]
        has_educational_content = any(
            keyword in text for keyword in educational_keywords
        )
        
        # 필수는 아니지만, 교육적 콘텐츠가 있으면 더 좋음
        return True, None
    
    def validate_question(self, question: str) -> Tuple[bool, Optional[str]]:
        """
        사용자 질문 검증
        Returns: (is_valid, error_message)
        """
        if not question or len(question.strip()) == 0:
            return False, "질문이 비어있습니다."
        
        # 질문 길이 검증
        if len(question) > 2000:
            return False, "질문이 너무 깁니다. 2000자 이하로 작성해주세요."
        
        question_lower = question.lower()
        
        # 1. 프롬프트 인젝션 방어
        if self.prompt_injection_pattern.search(question_lower):
            return False, "시스템 지시사항을 변경하려는 시도는 허용되지 않습니다. 강의 내용에 대한 질문만 가능합니다."
        
        # 2. 부적절한 키워드 필터링
        if self.forbidden_pattern.search(question_lower):
            return False, "부적절한 표현이 포함되어 있습니다. 정중한 언어로 질문해주세요."
        
        # 3. 컨텍스트 외 질문 감지 (경고만, 완전 차단은 아님)
        # 강의와 무관한 질문은 시스템 프롬프트에서 처리
        
        return True, None
    
    def sanitize_question(self, question: str) -> str:
        """
        질문 정제 (민감한 부분 제거)
        """
        sanitized = question.strip()
        
        # 프롬프트 인젝션 패턴 제거
        sanitized = self.prompt_injection_pattern.sub("", sanitized)
        
        # 금지 키워드 마스킹
        sanitized = self.forbidden_pattern.sub("[필터링됨]", sanitized)
        
        return sanitized.strip()


# 전역 Guardrails 인스턴스
guardrails = Guardrails()


def apply_guardrails(response: str) -> tuple[str, bool]:
    """
    가드레일 적용
    Returns: (filtered_response, is_safe)
    """
    is_safe, reason = guardrails.check_content(response)
    
    if not is_safe:
        # 안전하지 않은 경우 기본 메시지 반환
        return "죄송합니다. 적절한 답변을 생성할 수 없습니다.", False
    
    # 필터링 적용
    filtered = guardrails.filter_response(response)
    
    return filtered, True

