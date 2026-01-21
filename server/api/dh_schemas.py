"""
확장된 API 스키마
- 인증 관련 스키마
- 멀티 테넌트 관련 스키마
"""
from typing import Literal, Optional
import re

from pydantic import BaseModel, Field, field_validator

# 기존 스키마들 import
from api.schemas import (
    QueryRequest,
    ChatResponse,
    UploadResponse,
    StatusResponse,
)


# 인증 관련 스키마
class LoginRequest(BaseModel):
    """로그인 요청"""
    user_id: str = Field(..., description="사용자 ID")
    password: str = Field(..., description="비밀번호")
    role: Literal["instructor", "student"] = Field(..., description="사용자 역할")


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    expires_in: int = 86400  # 24시간


class RegisterInstructorRequest(BaseModel):
    """강사 등록 요청"""
    id: str = Field(..., description="강사 ID")
    name: str = Field(..., description="이름")
    email: str = Field(..., description="이메일")
    password: str = Field(..., min_length=8, description="비밀번호 (최소 8자)")
    profile_image_url: Optional[str] = Field(default=None, description="프로필 이미지 URL")
    bio: Optional[str] = Field(default=None, description="자기소개")
    specialization: str = Field(..., description="전문 분야 (필수)")
    # 회원가입 시 함께 등록할 수 있는 초기 강의 정보 (선택사항)
    initial_courses: Optional[list[dict]] = Field(default=None, description="초기 강의 정보 목록")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """간단한 이메일 형식 검증"""
        if not v:
            raise ValueError("이메일은 필수입니다.")
        # 기본적인 이메일 형식 검증
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return v


class UpdateInstructorRequest(BaseModel):
    """강사 프로필(개인정보) 수정 요청 - 보낸 필드만 변경"""
    name: Optional[str] = Field(default=None, description="이름")
    email: Optional[str] = Field(default=None, description="이메일")
    profile_image_url: Optional[str] = Field(default=None, description="프로필 이미지 URL")
    bio: Optional[str] = Field(default=None, description="자기소개")
    phone: Optional[str] = Field(default=None, description="전화번호")
    specialization: Optional[str] = Field(default=None, description="전문 분야")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """이메일 형식 검증 (선택 필드)"""
        if v is None:
            return v
        if not v.strip():
            return None
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return v


class RegisterStudentRequest(BaseModel):
    """학생 등록 요청"""
    id: str = Field(..., description="학생 ID")
    name: Optional[str] = None
    email: Optional[str] = None
    password: str = Field(..., description="비밀번호")


# 멀티 테넌트 관련 스키마
class EnrollCourseRequest(BaseModel):
    """강의 등록 요청"""
    course_id: str = Field(..., description="강의 ID")


class EnrollCourseResponse(BaseModel):
    """강의 등록 응답"""
    enrollment_id: int
    student_id: str
    course_id: str
    status: str
    enrolled_at: str


# 확장된 StatusResponse (진행률 포함)
class DetailedStatusResponse(StatusResponse):
    """상세 상태 응답 (진행률 포함)"""
    stage: Optional[str] = None
    error: Optional[str] = None


# 확장된 ChatResponse (가드레일 적용)
class SafeChatResponse(ChatResponse):
    """안전한 채팅 응답 (가드레일 적용)"""
    is_safe: bool = True
    filtered: bool = False


# 강사 정보 조회 응답
class InstructorProfileResponse(BaseModel):
    """강사 프로필 정보 응답"""
    id: str
    name: str
    email: str
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    created_at: str
    updated_at: str
    course_count: int = 0


# 강의 관련 스키마
class CreateCourseRequest(BaseModel):
    """강의 생성 요청"""
    course_id: str = Field(..., description="강의 ID")
    title: Optional[str] = Field(default=None, description="강의 제목")
    category: Optional[str] = Field(default=None, description="카테고리")
    total_chapters: Optional[int] = Field(default=None, description="전체 강의 수")


class UpdateCourseRequest(BaseModel):
    """강의 수정 요청"""
    title: Optional[str] = Field(default=None, description="강의 제목")
    category: Optional[str] = Field(default=None, description="카테고리")

