"""
개선된 API 엔드포인트
- 강사/학생 분리
- 권한 체크
- 멀티 테넌트 데이터 격리
- 가드레일 적용
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from fastapi.params import Form, File
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from pathlib import Path
from typing import Optional

from ai.pipelines.rag import RAGPipeline
from api.dh_schemas import (
    ChatResponse,
    QueryRequest,
    DetailedStatusResponse,
    UploadResponse,
    LoginRequest,
    TokenResponse,
    RegisterInstructorRequest,
    UpdateInstructorRequest,
    RegisterStudentRequest,
    EnrollCourseRequest,
    EnrollCourseResponse,
    SafeChatResponse,
    InstructorProfileResponse,
    CreateCourseRequest,
    UpdateCourseRequest,
)
from core.db import get_session, engine
from core.dh_auth import (
    get_current_user,
    require_instructor,
    require_student,
    require_any_user,
    verify_course_access,
    create_access_token,
    get_password_hash,
    verify_password,
)
from core.dh_guardrails import apply_guardrails
from core.dh_models import Student, CourseEnrollment, EnrollmentStatus
from core.dh_tasks import enqueue_processing_task
from core.models import Course, CourseStatus, Instructor, Video
from core.storage import save_course_assets
from ai.config import AISettings

router = APIRouter(prefix="", tags=["api"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_pipeline(settings: AISettings = Depends(AISettings)) -> RAGPipeline:
    return RAGPipeline(settings)


# ==================== 인증 엔드포인트 ====================

@router.post("/auth/register/instructor", response_model=TokenResponse)
async def register_instructor(
    payload: RegisterInstructorRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """강사 등록 - 프로필 정보와 함께 강사 계정 생성"""
    from datetime import datetime
    from core.db import init_db
    
    # 데이터베이스가 없으면 자동으로 생성
    init_db()
    
    # 기존 강사 확인 (ID 또는 이메일 중복 체크)
    existing_by_id = session.get(Instructor, payload.id)
    if existing_by_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instructor ID already exists",
        )
    
    # 이메일 중복 확인
    existing_by_email = session.exec(
        select(Instructor).where(Instructor.email == payload.email)
    ).first()
    if existing_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # 비밀번호 해싱
    password_hash = get_password_hash(payload.password)
    
    # 강사 생성 (프로필 정보 포함)
    # 빈 문자열을 None으로 변환
    profile_image_url = payload.profile_image_url.strip() if payload.profile_image_url and payload.profile_image_url.strip() else None
    bio = payload.bio.strip() if payload.bio and payload.bio.strip() else None
    phone = payload.phone.strip() if payload.phone and payload.phone.strip() else None
    specialization = payload.specialization.strip() if payload.specialization and payload.specialization.strip() else None
    
    instructor = Instructor(
        id=payload.id,
        name=payload.name,
        email=payload.email,
        password_hash=password_hash,
        profile_image_url=profile_image_url,
        bio=bio,
        phone=phone,
        specialization=specialization,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(instructor)
    session.commit()
    session.refresh(instructor)
    
    # 초기 강의 정보가 있으면 함께 등록
    if payload.initial_courses:
        from core.models import Course, CourseStatus
        for course_info in payload.initial_courses:
            course_id = course_info.get("course_id") or course_info.get("id")
            course_title = course_info.get("title") or course_info.get("name")
            if course_id and course_title:
                course = Course(
                    id=course_id,
                    instructor_id=instructor.id,
                    title=course_title,
                    status=CourseStatus.processing,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(course)
        session.commit()
    
    # JWT 토큰 생성
    token = create_access_token(
        data={"sub": instructor.id, "role": "instructor"}
    )
    
    return TokenResponse(
        access_token=token,
        user_id=instructor.id,
        role="instructor",
    )


@router.post("/auth/register/student", response_model=TokenResponse)
async def register_student(
    payload: RegisterStudentRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """학생 등록"""
    from core.db import init_db
    
    # 데이터베이스가 없으면 자동으로 생성
    init_db()
    # 기존 학생 확인
    existing = session.get(Student, payload.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already exists",
        )
    
    # 학생 생성
    student = Student(
        id=payload.id,
        name=payload.name,
        email=payload.email,
    )
    session.add(student)
    session.commit()
    
    # JWT 토큰 생성
    token = create_access_token(
        data={"sub": student.id, "role": "student"}
    )
    
    return TokenResponse(
        access_token=token,
        user_id=student.id,
        role="student",
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """로그인 - ID와 비밀번호로 인증"""
    if payload.role == "instructor":
        user = session.get(Instructor, payload.user_id)
        # 강사가 없으면 자동으로 생성
        if not user:
            user = Instructor(
                id=payload.user_id,
                name=payload.user_id,  # 기본값으로 ID 사용
                email=None,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
    elif payload.role == "student":
        user = session.get(Student, payload.user_id)
        # 학생이 없으면 자동으로 생성
        if not user:
            user = Student(
                id=payload.user_id,
                name=payload.user_id,  # 기본값으로 ID 사용
                email=None,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'instructor' or 'student'",
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials - User not found",
        )
    
    # 강사의 경우 비밀번호 검증
    if payload.role == "instructor":
        if not hasattr(user, "password_hash") or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials - Password not set",
            )
        
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials - Wrong password",
            )
    
    # 학생의 경우 비밀번호 검증 (향후 구현 예정)
    # elif payload.role == "student":
    #     if not hasattr(user, "password_hash") or not user.password_hash:
    #         raise HTTPException(...)
    #     if not verify_password(payload.password, user.password_hash):
    #         raise HTTPException(...)
    
    token = create_access_token(
        data={"sub": user.id, "role": payload.role}
    )
    
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=payload.role,
    )


# ==================== 강사 전용 엔드포인트 ====================

@router.post("/instructor/courses", response_model=dict)
async def instructor_create_course(
    payload: CreateCourseRequest,
    current_user: dict = Depends(require_instructor()),
    session: Session = Depends(get_session),
) -> dict:
    """강의 목록 생성 (파일 없이, 부모 강의만 생성)"""
    from datetime import datetime
    
    # 기존 강의 확인
    existing_course = session.get(Course, payload.course_id)
    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"강의 목록 ID '{payload.course_id}'가 이미 존재합니다.",
        )
    
    # 강사 정보 확인/생성
    instructor = session.get(Instructor, current_user["id"])
    if not instructor:
        instructor = Instructor(id=current_user["id"])
        session.add(instructor)
        session.commit()
    
    # 강의 목록 생성 (파일 없이, 상태는 completed로 설정 - 챕터를 추가할 수 있도록)
    # parent_course_id는 null (부모 강의이므로)
    course = Course(
        id=payload.course_id,
        instructor_id=current_user["id"],
        title=payload.title.strip() if payload.title and payload.title.strip() else None,
        category=payload.category.strip() if payload.category and payload.category.strip() else None,
        total_chapters=payload.total_chapters,  # 전체 강의 수 (참고용)
        parent_course_id=None,  # 부모 강의는 parent_course_id가 null
        status=CourseStatus.completed,  # 챕터를 추가할 수 있도록 completed 상태
        progress=0,
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    
    return {
        "message": "강의 목록이 생성되었습니다.",
        "course_id": course.id,
        "title": course.title,
        "category": course.category,
        "total_chapters": course.total_chapters,
    }


@router.post("/instructor/upload", response_model=UploadResponse)
async def instructor_upload(
    background_tasks: BackgroundTasks,
    instructor_id: str = Form(...),
    course_id: str = Form(...),
    instructor_name: Optional[str] = Form(None),
    course_title: str = Form(...),  # 필수 항목
    course_category: Optional[str] = Form(None),
    parent_course_id: Optional[str] = Form(None),  # 챕터인 경우 부모 강의 ID
    chapter_number: Optional[int] = Form(None),  # 챕터 번호
    video: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    pdf: UploadFile | None = File(None),
    smi: UploadFile | None = File(None),
    current_user: dict = Depends(require_instructor()),
    session: Session = Depends(get_session),
) -> UploadResponse:
    """강사용 파일 업로드 (권한 체크 포함) - 비디오와 오디오를 동시에 업로드 가능"""
    # 권한 확인: 자신의 강의만 업로드 가능
    if current_user["id"] != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload courses for yourself",
        )
    
    # Instructor/Course 확인 및 이름 업데이트
    instructor = session.get(Instructor, instructor_id)
    if not instructor:
        instructor = Instructor(
            id=instructor_id,
            name=instructor_name.strip() if instructor_name and instructor_name.strip() else None,
        )
        session.add(instructor)
    else:
        # 기존 강사가 있으면 이름 업데이트 (제공된 경우)
        if instructor_name and instructor_name.strip():
            instructor.name = instructor_name.strip()
    
    # 챕터인 경우 부모 강의 확인
    if parent_course_id:
        parent_course = session.get(Course, parent_course_id)
        if not parent_course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"부모 강의를 찾을 수 없습니다: {parent_course_id}"
            )
        if parent_course.instructor_id != instructor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="부모 강의가 다른 강사에게 속해 있습니다",
            )
    
    course = session.get(Course, course_id)
    if not course:
        # Course 생성 시 is_public 컬럼이 있으면 기본값 설정
        from sqlalchemy import inspect, text
        try:
            inspector = inspect(engine)
            if "course" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("course")]
                has_is_public = "is_public" in columns
            else:
                has_is_public = False
        except Exception:
            has_is_public = False
        
        if has_is_public:
            # is_public 컬럼이 있으면 SQL로 직접 INSERT
            from datetime import datetime
            session.execute(
                text("""
                    INSERT INTO course 
                    (id, instructor_id, title, category, parent_course_id, chapter_number, status, progress, created_at, updated_at, is_public)
                    VALUES 
                    (:id, :instructor_id, :title, :category, :parent_course_id, :chapter_number, :status, :progress, :created_at, :updated_at, 1)
                """),
                {
                    "id": course_id,
                    "instructor_id": instructor_id,
                    "title": course_title.strip() if course_title.strip() else course_id,
                    "category": course_category.strip() if course_category and course_category.strip() else None,
                    "parent_course_id": parent_course_id.strip() if parent_course_id and parent_course_id.strip() else None,
                    "chapter_number": chapter_number,
                    "status": CourseStatus.processing.value,
                    "progress": 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
            session.flush()
            course = session.get(Course, course_id)
        else:
            # is_public 컬럼이 없으면 일반 방식으로 생성
            course = Course(
                id=course_id,
                instructor_id=instructor_id,
                title=course_title.strip() if course_title.strip() else course_id,
                category=course_category.strip() if course_category and course_category.strip() else None,
                parent_course_id=parent_course_id.strip() if parent_course_id and parent_course_id.strip() else None,
                chapter_number=chapter_number,
            )
            session.add(course)
    elif course.instructor_id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Course belongs to another instructor",
        )
    else:
        # 기존 강의가 있으면 제목 및 카테고리 업데이트
        if course_title and course_title.strip():
            course.title = course_title.strip()
        elif not course.title:  # 제목이 없으면 course_id 사용
            course.title = course_id
        if course_category and course_category.strip():
            course.category = course_category.strip()
        if parent_course_id and parent_course_id.strip():
            course.parent_course_id = parent_course_id.strip()
        if chapter_number is not None:
            course.chapter_number = chapter_number
    
    course.status = CourseStatus.processing
    session.commit()
    
    # 파일 저장
    paths = save_course_assets(
        instructor_id=instructor_id,
        course_id=course_id,
        video=video,
        audio=audio,
        pdf=pdf,
        smi=smi,
    )
    
    # 백그라운드 작업 등록 (백엔드 A processor 호출)
    enqueue_processing_task(
        background_tasks,
        course_id=course_id,
        instructor_id=instructor_id,
        video_path=paths.get("video"),
        audio_path=paths.get("audio"),
        pdf_path=paths.get("pdf"),
        smi_path=paths.get("smi"),
    )
    
    return UploadResponse(
        course_id=course_id,
        instructor_id=instructor_id,
        status=course.status.value,
    )


@router.get("/instructor/courses", response_model=list[dict])
async def instructor_courses(
    current_user: dict = Depends(require_instructor()),
    session: Session = Depends(get_session),
) -> list[dict]:
    """강사의 강의 목록 조회 (자신의 강의만)"""
    courses = session.exec(
        select(Course).where(Course.instructor_id == current_user["id"])
    ).all()
    
    # 강사 정보 가져오기
    instructor = session.get(Instructor, current_user["id"])
    
    result = []
    for course in courses:
        # 챕터가 아닌 메인 강의만 표시
        if getattr(course, "parent_course_id", None) is None:
            # 챕터 개수 확인
            chapter_count = session.exec(
                select(Course).where(Course.parent_course_id == course.id)
            ).all()
            has_chapters = len(chapter_count) > 0
            
            result.append({
                "id": course.id,
                "title": course.title or course.id,
                "category": getattr(course, "category", None),
                "status": course.status.value,
                "created_at": course.created_at.isoformat() if course.created_at else None,
                "progress": getattr(course, "progress", 0),
                "instructor_name": instructor.name if instructor else None,
                "has_chapters": has_chapters,
                "chapter_count": len(chapter_count),
                "total_chapters": getattr(course, "total_chapters", None),
            })
    
    return result


@router.patch("/instructor/courses/{course_id}")
async def instructor_update_course(
    course_id: str,
    payload: UpdateCourseRequest,
    current_user: dict = Depends(require_instructor()),
    session: Session = Depends(get_session),
) -> dict:
    """강사가 자신의 강의 정보 수정 (제목, 카테고리)"""
    from datetime import datetime
    
    # 강의 확인 및 권한 체크
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"강의를 찾을 수 없습니다: {course_id}"
        )
    
    # 자신의 강의만 수정 가능
    if course.instructor_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 강사의 강의는 수정할 수 없습니다."
        )
    
    # 수정할 필드 업데이트
    if payload.title is not None:
        course.title = payload.title.strip() if payload.title.strip() else None
    if payload.category is not None:
        course.category = payload.category.strip() if payload.category.strip() else None
    
    course.updated_at = datetime.utcnow()
    session.add(course)
    session.commit()
    session.refresh(course)
    
    return {
        "message": "강의 정보가 수정되었습니다.",
        "course_id": course.id,
        "title": course.title,
        "category": course.category,
    }


@router.patch("/instructor/profile")
async def instructor_update_profile(
    payload: UpdateInstructorRequest,
    current_user: dict = Depends(require_instructor()),
    session: Session = Depends(get_session),
) -> dict:
    """강사가 자신의 프로필 정보 수정 (이름, 이메일)"""
    from datetime import datetime
    
    # 강사 확인
    instructor = session.get(Instructor, current_user["id"])
    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="강사 정보를 찾을 수 없습니다."
        )
    
    # 수정할 필드 업데이트
    if payload.name is not None:
        instructor.name = payload.name.strip() if payload.name.strip() else None
    if payload.email is not None:
        instructor.email = payload.email.strip() if payload.email.strip() else None
    
    session.add(instructor)
    session.commit()
    session.refresh(instructor)
    
    return {
        "message": "프로필 정보가 수정되었습니다.",
        "instructor_id": instructor.id,
        "name": instructor.name,
        "email": instructor.email,
    }


@router.delete("/instructor/courses/{course_id}")
async def instructor_delete_course(
    course_id: str,
    current_user: dict = Depends(require_instructor()),
    session: Session = Depends(get_session),
) -> dict:
    """강사가 자신의 강의 삭제 (권한 체크 포함)"""
    from pathlib import Path
    import shutil
    from core.config import AppSettings
    from ai.config import AISettings
    from ai.services.vectorstore import get_chroma_client, get_collection
    from core.models import Video, ChatSession
    
    # 1. 강의 확인 및 권한 체크
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"강의를 찾을 수 없습니다: {course_id}"
        )
    
    # 자신의 강의만 삭제 가능
    if course.instructor_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 강사의 강의는 삭제할 수 없습니다."
        )
    
    instructor_id = course.instructor_id
    
    # 2. 관련 데이터 삭제 (Video, ChatSession)
    videos = session.exec(select(Video).where(Video.course_id == course_id)).all()
    for video in videos:
        session.delete(video)
    
    sessions = session.exec(select(ChatSession).where(ChatSession.course_id == course_id)).all()
    for sess in sessions:
        session.delete(sess)
    
    # 3. 강의 삭제
    session.delete(course)
    session.commit()
    
    # 4. 벡터 DB에서 강의 데이터 삭제
    try:
        ai_settings = AISettings()
        client = get_chroma_client(ai_settings)
        collection = get_collection(client, ai_settings)
        
        # course_id로 필터링하여 삭제
        results = collection.get(where={"course_id": course_id})
        if results and results.get("ids"):
            collection.delete(ids=results["ids"])
    except Exception as e:
        print(f"벡터 DB 삭제 중 오류 (무시): {e}")
    
    # 5. 업로드 파일 삭제
    try:
        settings = AppSettings()
        uploads_dir = settings.uploads_dir
        
        course_dir = uploads_dir / instructor_id / course_id
        if course_dir.exists():
            shutil.rmtree(course_dir)
    except Exception as e:
        print(f"파일 삭제 중 오류 (무시): {e}")
    
    return {
        "message": f"강의 '{course_id}'가 삭제되었습니다.",
        "course_id": course_id,
    }


@router.get("/instructor/profile", response_model=InstructorProfileResponse)
async def get_instructor_profile(
    current_user: dict = Depends(require_instructor),
    session: Session = Depends(get_session),
) -> InstructorProfileResponse:
    """강사 프로필 정보 조회 (자신의 프로필만)"""
    instructor = session.get(Instructor, current_user["id"])
    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found",
        )
    
    # 강의 개수 조회
    course_count = len(session.exec(
        select(Course).where(Course.instructor_id == instructor.id)
    ).all())
    
    return InstructorProfileResponse(
        id=instructor.id,
        name=instructor.name or "",
        email=instructor.email or "",
        profile_image_url=instructor.profile_image_url,
        bio=instructor.bio,
        phone=instructor.phone,
        specialization=instructor.specialization,
        created_at=instructor.created_at.isoformat() if instructor.created_at else "",
        updated_at=instructor.updated_at.isoformat() if instructor.updated_at else "",
        course_count=course_count,
    )


# ==================== 학생 전용 엔드포인트 ====================

@router.post("/student/enroll", response_model=EnrollCourseResponse)
async def enroll_course(
    payload: EnrollCourseRequest,
    current_user: dict = Depends(require_student()),
    session: Session = Depends(get_session),
) -> EnrollCourseResponse:
    """강의 등록"""
    # 강의 존재 확인
    course = session.get(Course, payload.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    
    # 이미 등록되어 있는지 확인
    existing = session.exec(
        select(CourseEnrollment).where(
            CourseEnrollment.student_id == current_user["id"],
            CourseEnrollment.course_id == payload.course_id,
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course",
        )
    
    # 등록 생성
    enrollment = CourseEnrollment(
        student_id=current_user["id"],
        course_id=payload.course_id,
        status=EnrollmentStatus.active,
    )
    session.add(enrollment)
    session.commit()
    
    return EnrollCourseResponse(
        enrollment_id=enrollment.id or 0,
        student_id=enrollment.student_id,
        course_id=enrollment.course_id,
        status=enrollment.status.value,
        enrolled_at=enrollment.enrolled_at.isoformat(),
    )


@router.get("/student/courses", response_model=list[dict])
async def student_courses(
    current_user: dict = Depends(require_student()),
    session: Session = Depends(get_session),
) -> list[dict]:
    """학생이 등록한 강의 목록 조회"""
    enrollments = session.exec(
        select(CourseEnrollment).where(
            CourseEnrollment.student_id == current_user["id"],
            CourseEnrollment.status == EnrollmentStatus.active,
        )
    ).all()
    
    courses = []
    for enrollment in enrollments:
        course = session.get(Course, enrollment.course_id)
        if course:
            courses.append({
                "id": course.id,
                "title": course.title,
                "status": course.status.value,
                "enrolled_at": enrollment.enrolled_at.isoformat(),
            })
    
    return courses


# ==================== 공통 엔드포인트 ====================

@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "Yeop-Gang"}


@router.get("/status/{course_id}", response_model=DetailedStatusResponse)
async def get_status(
    course_id: str,
    current_user: dict = Depends(require_any_user()),
    session: Session = Depends(get_session),
) -> DetailedStatusResponse:
    """처리 상태 조회 (권한 체크 포함)"""
    # 강의 접근 권한 확인
    await verify_course_access(course_id, current_user, session)
    
    course = session.get(Course, course_id)
    if not course:
        return DetailedStatusResponse(
            course_id=course_id,
            status="not_found",
            progress=0,
        )
    
    # 실제 진행도 필드 사용
    progress = getattr(course, 'progress', 0) if course.status == CourseStatus.processing else 100
    return DetailedStatusResponse(
        course_id=course_id,
        status=course.status.value,
        progress=progress,
    )


@router.get("/video/{course_id}")
async def get_video(
    course_id: str,
    current_user: dict = Depends(require_any_user()),
    session: Session = Depends(get_session),
) -> FileResponse:
    """비디오/오디오 파일 조회 (권한 체크 포함) - mp4와 mp3 모두 지원"""
    # 강의 접근 권한 확인
    await verify_course_access(course_id, current_user, session)
    
    course = session.get(Course, course_id)
    if course:
        # 우선 video 타입 파일 확인 (mp4 우선)
        videos = session.exec(
            select(Video).where(
                Video.course_id == course_id,
                Video.filetype == "video"
            )
        ).all()
        for vid in videos:
            video_path = Path(vid.storage_path)
            if video_path.exists():
                suffix = video_path.suffix.lower()
                if suffix == ".mp4":
                    return FileResponse(video_path, media_type="video/mp4")
                elif suffix in [".avi", ".mov", ".mkv", ".webm"]:
                    return FileResponse(video_path, media_type="video/mp4")  # 기본 비디오 타입
        
        # audio 타입 파일 확인 (mp3 포함)
        audios = session.exec(
            select(Video).where(
                Video.course_id == course_id,
                Video.filetype == "audio"
            )
        ).all()
        for audio in audios:
            audio_path = Path(audio.storage_path)
            if audio_path.exists():
                suffix = audio_path.suffix.lower()
                if suffix == ".mp3":
                    return FileResponse(audio_path, media_type="audio/mpeg")
                elif suffix == ".wav":
                    return FileResponse(audio_path, media_type="audio/wav")
                elif suffix in [".m4a", ".aac", ".ogg", ".flac"]:
                    return FileResponse(audio_path, media_type="audio/mpeg")
    
    # Fallback
    ref_video = PROJECT_ROOT / "ref" / "video" / "testvedio_1.mp4"
    if ref_video.exists():
        return FileResponse(ref_video, media_type="video/mp4")
    
    raise HTTPException(status_code=404, detail="Video/Audio not found")


@router.post("/chat/ask", response_model=SafeChatResponse)
async def ask(
    payload: QueryRequest,
    current_user: dict = Depends(require_any_user()),
    pipeline: RAGPipeline = Depends(get_pipeline),
    session: Session = Depends(get_session),
) -> SafeChatResponse:
    """챗봇 질의 (권한 체크 및 가드레일 적용)"""
    # 강의 접근 권한 확인
    await verify_course_access(payload.course_id, current_user, session)
    
    conversation_id = payload.conversation_id or f"{current_user['id']}:{payload.course_id}"
    
    # 간단한 대화 히스토리 (프로덕션에서는 DB 사용)
    if not hasattr(ask, '_conversation_history'):
        setattr(ask, '_conversation_history', {})
    history = getattr(ask, '_conversation_history', {}).get(conversation_id, [])
    
    # 질문 분석: 인사말인지, 긍정적 피드백인지 확인
    question_lower = payload.question.lower().strip()
    question_trimmed = payload.question.strip()
    
    # 인사말 키워드 (간단한 인사만, 불필요한 설명 없이)
    greeting_keywords = [
        "안녕", "안녕하세요", "안녕하셔", "안녕하십니까",
        "쌤 안녕", "쌤안녕", "선생님 안녕", "선생님안녕",
        "하이", "hi", "hello"
    ]
    is_greeting = any(kw in question_lower for kw in greeting_keywords) and len(question_trimmed) < 20
    
    # 인사말이면 간단하게만 답변
    if is_greeting:
        answer = "안녕하세요! 궁금한 점이 있으면 언제든지 물어보세요. 😊"
        
        # 대화 히스토리 업데이트
        history.append({"role": "user", "content": payload.question})
        history.append({"role": "assistant", "content": answer})
        if len(history) > 20:
            history = history[-20:]
        getattr(ask, '_conversation_history', {})[conversation_id] = history
        
        return SafeChatResponse(
            answer=answer,
            sources=[],
            conversation_id=conversation_id,
            course_id=payload.course_id,
            is_safe=True,
            filtered=False,
        )
    
    # 긍정적 피드백 키워드 (간단하게 답변, API 호출 없이 템플릿 응답)
    positive_feedback_keywords = [
        "이해가 가", "이해가 되", "알았", "알겠", "이해했", "이해됐", 
        "이해했어", "알겠어", "이해됐어", "이해가 돼", "이해가 되네",
        "좋아", "좋아요", "감사", "고마워", "고마워요", "네", "응", "예",
        "이제 알았", "이제 알겠", "이제 이해했", "이제 이해했어", "이제 이해됐",
        "아하 이해", "아하 알았", "아하 알겠", "이해됐어요", "이해가 됐어요",
        "이해가 됐", "알겠어요", "알았어요", "이해했어요"
    ]
    is_positive_feedback = any(kw in question_lower for kw in positive_feedback_keywords)
    
    # 긍정적 피드백이면 API 호출 없이 바로 템플릿 응답 반환
    if is_positive_feedback:
        answer = "좋아요! 잘 이해하셨네요. 궁금한 점이 더 있으면 언제든지 물어보세요. 😊"
        
        # 대화 히스토리 업데이트
        history.append({"role": "user", "content": payload.question})
        history.append({"role": "assistant", "content": answer})
        if len(history) > 20:
            history = history[-20:]
        getattr(ask, '_conversation_history', {})[conversation_id] = history
        
        return SafeChatResponse(
            answer=answer,
            sources=[],
            conversation_id=conversation_id,
            course_id=payload.course_id,
            is_safe=True,
            filtered=False,
        )
    
    # RAG 쿼리 실행
    result = pipeline.query(
        payload.question,
        course_id=payload.course_id,
        conversation_history=history
    )
    
    answer = result.get("answer", "")
    
    # 가드레일 적용
    filtered_answer, is_safe = apply_guardrails(answer)
    filtered = answer != filtered_answer
    
    # 대화 히스토리 업데이트
    history.append({"role": "user", "content": payload.question})
    history.append({"role": "assistant", "content": filtered_answer})
    if len(history) > 20:
        history = history[-20:]
    getattr(ask, '_conversation_history', {})[conversation_id] = history
    
    return SafeChatResponse(
        answer=filtered_answer,
        sources=[str(src) for src in result.get("documents", [])],
        conversation_id=conversation_id,
        course_id=payload.course_id,
        is_safe=is_safe,
        filtered=filtered,
    )

