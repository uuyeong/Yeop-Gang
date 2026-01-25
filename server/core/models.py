from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class CourseStatus(str, Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"


class UserRole(str, Enum):
    instructor = "instructor"
    student = "student"


class Instructor(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    name: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = Field(default=None, description="비밀번호 해시")
    profile_image_url: Optional[str] = Field(default=None, description="프로필 이미지 URL")
    bio: Optional[str] = Field(default=None, description="자기소개")
    phone: Optional[str] = Field(default=None, description="전화번호")
    specialization: Optional[str] = Field(default=None, description="전문 분야")
    persona_profile: Optional[str] = Field(default=None, description="강사 기본 스타일 분석 결과 (JSON 문자열) - 첫 강의에서 추출하여 재사용")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    courses: list["Course"] = Relationship(back_populates="instructor")


class Course(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    instructor_id: str = Field(foreign_key="instructor.id")
    title: Optional[str] = None
    category: Optional[str] = Field(default=None, index=True, description="강의 과목")
    total_chapters: Optional[int] = Field(
        default=None,
        description="전체 강의 수 (참고용, 부모 강의에만 사용)"
    )
    parent_course_id: Optional[str] = Field(
        default=None, 
        foreign_key="course.id", 
        index=True,
        description="부모 강의 ID (챕터인 경우)"
    )
    chapter_number: Optional[int] = Field(
        default=None,
        description="챕터 번호 (1, 2, 3...)"
    )
    status: CourseStatus = Field(default=CourseStatus.processing)
    progress: int = Field(default=0, description="처리 진행도 (0-100)")  # 0-100%
    persona_profile: Optional[str] = Field(default=None, description="강사 스타일 분석 결과 (JSON 문자열)")
    error_message: Optional[str] = Field(
        default=None,
        description="처리 실패 시 사용자에게 노출할 상세 메시지",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    instructor: Instructor = Relationship(back_populates="courses")
    videos: list["Video"] = Relationship(back_populates="course")
    sessions: list["ChatSession"] = Relationship(back_populates="course")


class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: str = Field(foreign_key="course.id")
    filename: str
    filetype: str = Field(default="video")  # video | pdf
    storage_path: str
    transcript_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    course: Course = Relationship(back_populates="videos")


class ChatSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: str = Field(foreign_key="course.id")
    user_role: UserRole = Field(default=UserRole.student)
    status: CourseStatus = Field(default=CourseStatus.completed)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    course: Course = Relationship(back_populates="sessions")


# dh: Student 모델은 server/core/dh_models.py에 정의됨
