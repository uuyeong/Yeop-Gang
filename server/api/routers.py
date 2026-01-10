# dh: 이 파일은 기존 호환성을 위해 유지됩니다.
# dh: 새로운 보안 기능이 포함된 API는 server/api/dh_routers.py를 사용하세요.

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, Request, HTTPException
from fastapi.params import Form, File
from fastapi.responses import FileResponse, StreamingResponse, Response
from sqlmodel import Session, select
from pathlib import Path
from typing import Optional
import os
import re

from ai.pipelines.rag import RAGPipeline
from api.schemas import (
    ChatResponse,
    QueryRequest,
    StatusResponse,
    UploadResponse,
    SummaryRequest,
    SummaryResponse,
    QuizRequest,
    QuizResponse,
    QuizSubmitRequest,
    QuizResult,
    RegisterInstructorRequest,
    LoginRequest,
    TokenResponse,
)
from datetime import datetime
from core.db import get_session
from core.models import Course, CourseStatus, Instructor, Video
from core.storage import save_course_assets
from core.tasks import enqueue_processing_task
from core.dh_auth import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from ai.config import AISettings

router = APIRouter(prefix="", tags=["api"])

# server 폴더 기준 경로
SERVER_ROOT = Path(__file__).resolve().parent.parent
# 프로젝트 루트 (ref 폴더 등에 사용)
PROJECT_ROOT = SERVER_ROOT.parent


def get_pipeline(settings: AISettings = Depends(AISettings)) -> RAGPipeline:
    return RAGPipeline(settings)


def _serve_video_file(file_path: Path, media_type: str):
    """
    FastAPI FileResponse를 사용하여 비디오 파일 제공
    FileResponse는 자동으로 HTTP Range 요청을 처리합니다.
    """
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
        }
    )


# ==================== 인증 엔드포인트 ====================

@router.post("/auth/register/instructor", response_model=TokenResponse)
async def register_instructor(
    payload: RegisterInstructorRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """강사 등록 - 프로필 정보와 함께 강사 계정 생성"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"강사 회원가입 시도: ID={payload.id}, Email={payload.email}")
        
        # 기존 강사 확인 (ID 또는 이메일 중복 체크)
        existing_by_id = session.get(Instructor, payload.id)
        if existing_by_id:
            logger.warning(f"강사 ID 중복: {payload.id}")
            raise HTTPException(
                status_code=400,
                detail="이미 존재하는 강사 ID입니다.",
            )
        
        # 이메일 중복 확인
        existing_by_email = session.exec(
            select(Instructor).where(Instructor.email == payload.email)
        ).first()
        if existing_by_email:
            logger.warning(f"이메일 중복: {payload.email}")
            raise HTTPException(
                status_code=400,
                detail="이미 등록된 이메일입니다.",
            )
        
        # 비밀번호 해싱
        try:
            password_hash = get_password_hash(payload.password)
        except Exception as e:
            logger.error(f"비밀번호 해싱 실패: {e}")
            raise HTTPException(
                status_code=500,
                detail="비밀번호 처리 중 오류가 발생했습니다.",
            )
        
        # 강사 생성 (프로필 정보 포함)
        try:
            instructor = Instructor(
                id=payload.id,
                name=payload.name,
                email=payload.email,
                password_hash=password_hash,
                profile_image_url=payload.profile_image_url,
                bio=payload.bio,
                phone=payload.phone,
                specialization=payload.specialization,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(instructor)
            session.commit()
            session.refresh(instructor)
            logger.info(f"강사 생성 성공: ID={instructor.id}")
        except Exception as e:
            session.rollback()
            logger.error(f"강사 생성 실패: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"강사 등록 중 오류가 발생했습니다: {str(e)}",
            )
        
        # 초기 강의 정보가 있으면 함께 등록
        if payload.initial_courses:
            try:
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
            except Exception as e:
                session.rollback()
                logger.error(f"강의 등록 실패: {e}")
                # 강의 등록 실패해도 강사 등록은 성공한 것으로 처리
        
        # JWT 토큰 생성
        try:
            token = create_access_token(
                data={"sub": instructor.id, "role": "instructor"}
            )
        except Exception as e:
            logger.error(f"토큰 생성 실패: {e}")
            raise HTTPException(
                status_code=500,
                detail="토큰 생성 중 오류가 발생했습니다.",
            )
        
        logger.info(f"강사 회원가입 완료: ID={instructor.id}")
        return TokenResponse(
            access_token=token,
            user_id=instructor.id,
            role="instructor",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"서버 오류가 발생했습니다: {str(e)}",
        )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """로그인 - ID와 비밀번호로 인증"""
    if payload.role == "instructor":
        user = session.get(Instructor, payload.user_id)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials - User not found",
            )
        
        # 비밀번호 검증
        if not hasattr(user, "password_hash") or not user.password_hash:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials - Password not set",
            )
        
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials - Wrong password",
            )
    elif payload.role == "student":
        from core.dh_models import Student
        user = session.get(Student, payload.user_id)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials - User not found",
            )
        # 학생 비밀번호 검증은 향후 구현 예정
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Must be 'instructor' or 'student'",
        )
    
    token = create_access_token(
        data={"sub": user.id, "role": payload.role}
    )
    
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=payload.role,
    )


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "Yeop-Gang"}


@router.get("/courses")
def list_courses(
    q: Optional[str] = None,
    category: Optional[str] = None,
    session: Session = Depends(get_session),
) -> list[dict]:
    """
    모든 강의 목록 조회 (학생용)
    - q: 검색어 (강의명, 강사명으로 검색)
    - category: 카테고리 필터
    """
    from sqlmodel import or_
    
    query = select(Course)
    
    # 검색어 필터 (SQLite는 ilike가 없으므로 contains 사용)
    if q:
        # 강의명 또는 강의 ID로 검색
        query = query.where(
            or_(
                Course.title.contains(q) if Course.title else False,
                Course.id.contains(q),
            )
        )
    
    # 카테고리 필터
    if category:
        query = query.where(Course.category == category)
    
    # 챕터가 아닌 메인 강의만 조회 (parent_course_id가 null인 것만)
    query = query.where(Course.parent_course_id.is_(None))
    
    courses = session.exec(query).all()
    
    # 강사 정보도 함께 가져오기
    result = []
    for course in courses:
        instructor = session.get(Instructor, course.instructor_id)
        # 검색어가 강사명과 일치하는지 확인
        if q and instructor and instructor.name:
            if q.lower() not in instructor.name.lower():
                continue
        
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
            "instructor_id": course.instructor_id,
            "instructor_name": instructor.name if instructor else None,
            "created_at": course.created_at.isoformat() if course.created_at else None,
            "progress": getattr(course, "progress", 0),
            "has_chapters": has_chapters,
            "chapter_count": len(chapter_count),
            "total_chapters": getattr(course, "total_chapters", None),
        })
    
    return result


@router.get("/courses/{course_id}")
def get_course(
    course_id: str,
    session: Session = Depends(get_session),
) -> dict:
    """
    단일 강의 정보 조회
    DB에 없어도 파일 시스템에서 기본 정보 반환
    """
    course = session.get(Course, course_id)
    
    if course:
        # 강사 정보 가져오기
        instructor = session.get(Instructor, course.instructor_id)
        
        return {
            "id": course.id,
            "title": course.title or course.id,
            "category": getattr(course, "category", None),
            "instructor_id": course.instructor_id,
            "instructor_name": instructor.name if instructor else None,
            "status": course.status.value,
            "progress": getattr(course, "progress", 0),
            "created_at": course.created_at.isoformat() if course.created_at else None,
        }
    
    # DB에 없으면 파일 시스템에서 확인하여 기본 정보 반환
    from core.config import AppSettings
    settings = AppSettings()
    
    # 여러 가능한 instructor_id 경로 시도
    possible_instructor_ids = [
        "test-instructor-1",
        "test-instructor",
    ]
    # course_id에서 추론 (test-course-1 -> test-instructor-1)
    if "-" in course_id:
        base_name = course_id.split("-")[0]
        possible_instructor_ids.append(f"{base_name}-instructor-1")
        possible_instructor_ids.append(f"{base_name}-instructor")
    
    for instructor_id in possible_instructor_ids:
        if not instructor_id:
            continue
        course_dir = settings.uploads_dir / instructor_id / course_id
        if course_dir.exists():
            # 파일 시스템에 강의 디렉토리가 있으면 기본 정보 반환
            return {
                "id": course_id,
                "title": course_id.replace("-", " ").title(),
                "category": None,
                "instructor_id": instructor_id,
                "instructor_name": None,
                "status": "completed",
                "progress": 100,
                "created_at": None,
            }
    
    # 파일 시스템에도 없으면 404 반환
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"강의를 찾을 수 없습니다: {course_id}")


@router.get("/courses/{course_id}/chapters")
def get_course_chapters(
    course_id: str,
    session: Session = Depends(get_session),
) -> dict:
    """
    강의의 챕터 목록 조회
    """
    # 메인 강의 확인
    main_course = session.get(Course, course_id)
    if not main_course:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"강의를 찾을 수 없습니다: {course_id}")
    
    # 강사 정보 가져오기
    instructor = session.get(Instructor, main_course.instructor_id)
    
    # 챕터 목록 조회 (parent_course_id가 course_id인 것들)
    chapters = session.exec(
        select(Course)
        .where(Course.parent_course_id == course_id)
        .order_by(Course.chapter_number.asc())
    ).all()
    
    return {
        "course": {
            "id": main_course.id,
            "title": main_course.title or main_course.id,
            "category": getattr(main_course, "category", None),
            "instructor_id": main_course.instructor_id,
            "instructor_name": instructor.name if instructor else None,
            "total_chapters": getattr(main_course, "total_chapters", None),
        },
        "chapters": [
            {
                "id": chapter.id,
                "title": chapter.title or chapter.id,
                "chapter_number": getattr(chapter, "chapter_number", None),
                "status": chapter.status.value,
                "progress": getattr(chapter, "progress", 0),
                "created_at": chapter.created_at.isoformat() if chapter.created_at else None,
            }
            for chapter in chapters
        ],
    }


@router.delete("/courses/{course_id}")
def delete_course(course_id: str, session: Session = Depends(get_session)) -> dict:
    """
    강의 삭제 (DB, 벡터 DB, 업로드 파일 모두 삭제)
    """
    from pathlib import Path
    import shutil
    from core.config import AppSettings
    from ai.config import AISettings
    from ai.services.vectorstore import get_chroma_client, get_collection
    
    # 1. DB에서 강의 확인
    course = session.get(Course, course_id)
    if not course:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"강의를 찾을 수 없습니다: {course_id}")
    
    instructor_id = course.instructor_id
    
    # 2. 관련 데이터 삭제 (Video, ChatSession)
    videos = session.exec(select(Video).where(Video.course_id == course_id)).all()
    for video in videos:
        session.delete(video)
    
    from core.models import ChatSession
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


@router.post("/upload", response_model=UploadResponse)
async def upload_course_assets(
    background_tasks: BackgroundTasks,
    instructor_id: str = Form(...),
    course_id: str = Form(...),
    video: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    pdf: UploadFile | None = File(None),
    session: Session = Depends(get_session),
) -> UploadResponse:
    # Ensure instructor/course exist
    instructor = session.get(Instructor, instructor_id)
    if not instructor:
        instructor = Instructor(id=instructor_id)
        session.add(instructor)

    course = session.get(Course, course_id)
    if not course:
        course = Course(id=course_id, instructor_id=instructor_id)
        session.add(course)
    course.status = CourseStatus.processing
    session.commit()

    paths = save_course_assets(
        instructor_id=instructor_id,
        course_id=course_id,
        video=video,
        audio=audio,
        pdf=pdf,
    )

    enqueue_processing_task(
        background_tasks,
        course_id=course_id,
        instructor_id=instructor_id,
        video_path=paths.get("video"),
        audio_path=paths.get("audio"),
        pdf_path=paths.get("pdf"),
    )
    return UploadResponse(
        course_id=course_id,
        instructor_id=instructor_id,
        status=course.status.value,
    )


@router.get("/status/{course_id}", response_model=StatusResponse)
def status(course_id: str, session: Session = Depends(get_session)) -> StatusResponse:
    course = session.get(Course, course_id)
    if not course:
        return StatusResponse(course_id=course_id, status="not_found", progress=0, message="강의를 찾을 수 없습니다.")

    # 실제 진행도 필드 사용
    progress = getattr(course, 'progress', 0) if course.status == CourseStatus.processing else 100
    
    # 실패 상태일 때 도움말 메시지 추가
    message = None
    if course.status == CourseStatus.failed:
        message = "서버 로그를 확인하세요. 일반적인 원인: OPENAI_API_KEY 미설정, 파일 형식 오류, 네트워크 문제"
    
    return StatusResponse(
        course_id=course_id,
        status=course.status.value,
        progress=progress,
        message=message,
    )


# 간단한 메모리 기반 대화 히스토리 저장소 (프로덕션에서는 DB 사용 권장)
_conversation_history: dict[str, list[dict[str, str]]] = {}


@router.get("/video/{course_id}")
def get_video(course_id: str, session: Session = Depends(get_session)):
    """
    Get video/audio file for a course. Returns the first video or audio file found for the course.
    Supports both mp4 (video) and mp3 (audio) files.
    For testing: can also serve files from ref/video/ folder.
    Also searches filesystem if course is not in DB.
    """
    import logging
    from core.config import AppSettings
    
    logger = logging.getLogger(__name__)
    settings = AppSettings()
    logger.info(f"Requesting video for course_id: {course_id}")
    
    # Try to get video/audio from database
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
            # storage_path가 절대 경로인지 상대 경로인지 확인
            video_path = Path(vid.storage_path)
            if not video_path.is_absolute():
                # 상대 경로인 경우
                # storage_path가 상대 경로면 uploads_dir 기준으로 절대 경로 변환
                if not video_path.is_absolute():
                    video_path = settings.uploads_dir / video_path
            else:
                video_path = video_path.resolve()
            
            if video_path.exists():
                suffix = video_path.suffix.lower()
                logger.info(f"Found video file: {video_path} (suffix: {suffix})")
                if suffix == ".mp4":
                    return _serve_video_file(video_path, "video/mp4")
                elif suffix in [".avi", ".mov", ".mkv", ".webm"]:
                    return _serve_video_file(video_path, "video/mp4")
            else:
                # 디버그 레벨로 변경 (너무 많은 경고 방지)
                logger.debug(f"Video file not found at path: {video_path}")
        
        # audio 타입 파일 확인 (mp3 포함)
        audios = session.exec(
            select(Video).where(
                Video.course_id == course_id,
                Video.filetype == "audio"
            )
        ).all()
        for audio in audios:
            # storage_path가 절대 경로인지 상대 경로인지 확인
            audio_path = Path(audio.storage_path)
            if not audio_path.is_absolute():
                # 상대 경로인 경우
                # storage_path가 상대 경로면 uploads_dir 기준으로 절대 경로 변환
                if not audio_path.is_absolute():
                    audio_path = settings.uploads_dir / audio_path
            else:
                audio_path = audio_path.resolve()
            
            if audio_path.exists():
                suffix = audio_path.suffix.lower()
                logger.info(f"Found audio file: {audio_path} (suffix: {suffix})")
                if suffix == ".mp3":
                    return FileResponse(
                        audio_path, 
                        media_type="audio/mpeg",
                        headers={
                            "Accept-Ranges": "bytes",
                            "Content-Length": str(audio_path.stat().st_size),
                        }
                    )
                elif suffix == ".wav":
                    return FileResponse(
                        audio_path, 
                        media_type="audio/wav",
                        headers={
                            "Accept-Ranges": "bytes",
                            "Content-Length": str(audio_path.stat().st_size),
                        }
                    )
                elif suffix in [".m4a", ".aac", ".ogg", ".flac"]:
                    return FileResponse(
                        audio_path, 
                        media_type="audio/mpeg",
                        headers={
                            "Accept-Ranges": "bytes",
                            "Content-Length": str(audio_path.stat().st_size),
                        }
                    )
            else:
                # 디버그 레벨로 변경 (너무 많은 경고 방지)
                logger.debug(f"Audio file not found at path: {audio_path}")
        
        # DB에 레코드는 있지만 파일이 없는 경우, 파일 시스템에서 직접 찾기
        # instructor_id/course_id 구조로 찾기
        if course.instructor_id:
            course_dir = settings.uploads_dir / course.instructor_id / course_id
            if course_dir.exists():
                logger.info(f"Searching for files in: {course_dir}")
                # mp4 파일 찾기
                for video_file in course_dir.glob("*.mp4"):
                    if video_file.exists():
                        logger.info(f"Found video file via filesystem search: {video_file}")
                        return _serve_video_file(video_file, "video/mp4")
                # 다른 비디오 형식 찾기
                for ext in [".avi", ".mov", ".mkv", ".webm"]:
                    for video_file in course_dir.glob(f"*{ext}"):
                        if video_file.exists():
                            logger.info(f"Found video file via filesystem search: {video_file}")
                            return _serve_video_file(video_file, "video/mp4")
                # mp3 파일 찾기
                for audio_file in course_dir.glob("*.mp3"):
                    if audio_file.exists():
                        logger.info(f"Found audio file via filesystem search: {audio_file}")
                        return FileResponse(
                            audio_file, 
                            media_type="audio/mpeg",
                            headers={
                                "Accept-Ranges": "bytes",
                                "Content-Length": str(audio_file.stat().st_size),
                            }
                        )
                # 다른 오디오 형식 찾기
                for ext in [".wav", ".m4a", ".aac", ".ogg", ".flac"]:
                    for audio_file in course_dir.glob(f"*{ext}"):
                        if audio_file.exists():
                            logger.info(f"Found audio file via filesystem search: {audio_file}")
                            return FileResponse(
                                audio_file, 
                                media_type="audio/mpeg",
                                headers={
                                    "Accept-Ranges": "bytes",
                                    "Content-Length": str(audio_file.stat().st_size),
                                }
                            )
    
    # DB에 강의가 없어도 파일 시스템에서 직접 찾기 시도
    # 여러 가능한 instructor_id 경로 시도
    possible_instructor_ids = [
        "test-instructor-1",
        "test-instructor",
    ]
    # course_id에서 추론 (test-course-1 -> test-instructor-1)
    if "-" in course_id:
        base_name = course_id.split("-")[0]
        possible_instructor_ids.append(f"{base_name}-instructor-1")
        possible_instructor_ids.append(f"{base_name}-instructor")
    
    logger.info(f"Course not in DB, searching filesystem with possible instructor_ids: {possible_instructor_ids}")
    
    for instructor_id in possible_instructor_ids:
        if not instructor_id:
            continue
        course_dir = settings.uploads_dir / instructor_id / course_id
        if course_dir.exists():
            logger.info(f"Searching for files in: {course_dir}")
            # mp4 파일 찾기
            for video_file in course_dir.glob("*.mp4"):
                if video_file.exists():
                    logger.info(f"Found video file via filesystem search: {video_file}")
                    return _serve_video_file(video_file, "video/mp4")
            # 다른 비디오 형식 찾기
            for ext in [".avi", ".mov", ".mkv", ".webm"]:
                for video_file in course_dir.glob(f"*{ext}"):
                    if video_file.exists():
                        logger.info(f"Found video file via filesystem search: {video_file}")
                        return _serve_video_file(video_file, "video/mp4")
            # mp3 파일 찾기
            for audio_file in course_dir.glob("*.mp3"):
                if audio_file.exists():
                    logger.info(f"Found audio file via filesystem search: {audio_file}")
                    return FileResponse(
                        audio_file, 
                        media_type="audio/mpeg",
                        headers={
                            "Accept-Ranges": "bytes",
                            "Content-Length": str(audio_file.stat().st_size),
                        }
                    )
            # 다른 오디오 형식 찾기
            for ext in [".wav", ".m4a", ".aac", ".ogg", ".flac"]:
                for audio_file in course_dir.glob(f"*{ext}"):
                    if audio_file.exists():
                        logger.info(f"Found audio file via filesystem search: {audio_file}")
                        return FileResponse(
                            audio_file, 
                            media_type="audio/mpeg",
                            headers={
                                "Accept-Ranges": "bytes",
                                "Content-Length": str(audio_file.stat().st_size),
                            }
                        )
    
    # Fallback: try ref/video folder for testing
    ref_video = PROJECT_ROOT / "ref" / "video" / "testvedio_1.mp4"
    if ref_video.exists():
        logger.info(f"Using fallback video file: {ref_video}")
        return _serve_video_file(ref_video, "video/mp4")
    
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Video/Audio not found for course_id: {course_id}")


@router.post("/chat/ask", response_model=ChatResponse)
def ask(
    payload: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
    session: Session = Depends(get_session),
) -> ChatResponse:
    conversation_id = payload.conversation_id or "default"
    
    # 대화 히스토리 가져오기
    history = _conversation_history.get(conversation_id, [])
    
    # 질문 분석: 인사말인지, 긍정적 피드백인지, 대화 히스토리 질문인지 확인
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
        if len(history) > 50:
            history = history[-50:]
        _conversation_history[conversation_id] = history
        
        return ChatResponse(
            answer=answer,
            sources=[],
            conversation_id=conversation_id,
            course_id=payload.course_id,
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
        # 대화 히스토리에 최근 assistant 답변이 있으면 그것을 참고하여 더 자연스럽게 응답
        if history and len(history) > 0:
            recent_assistant = next(
                (msg.get("content", "") for msg in reversed(history[-5:]) if msg.get("role") == "assistant"),
                None
            )
            if recent_assistant:
                answer = "좋아요! 잘 이해하셨네요. 궁금한 점이 더 있으면 언제든지 물어보세요. 😊"
            else:
                answer = "좋아요! 궁금한 점이 더 있으면 언제든지 물어보세요. 😊"
        else:
            answer = "좋아요! 궁금한 점이 더 있으면 언제든지 물어보세요. 😊"
        
        # 대화 히스토리 업데이트
        history.append({"role": "user", "content": payload.question})
        history.append({"role": "assistant", "content": answer})
        if len(history) > 50:
            history = history[-50:]
        _conversation_history[conversation_id] = history
        
        return ChatResponse(
            answer=answer,
            sources=[],
            conversation_id=conversation_id,
            course_id=payload.course_id,
        )
    
    # 대화 히스토리 관련 질문
    history_question_keywords = [
        "방금 한 말", "방금 말한", "방금 말씀", "방금 한 말씀",
        "아까 말한", "아까 한 말", "아까 말씀", "아까 한 말씀",
        "지금까지", "지금까지 한 말", "지금까지 말한", "지금까지 대화",
        "무슨 말", "뭐라고", "뭐라고 했", "뭐라고 하셨", "뭐라고 말씀"
    ]
    is_history_question = any(kw in question_lower for kw in history_question_keywords)
    
    # 과거 질문 반복 확인 (API 호출 없이 이전 답변 재사용)
    is_repeated_question = False
    previous_answer = None
    if history:
        # 최근 사용자 질문들과 비교
        recent_user_questions = []
        recent_answers = []
        for i, msg in enumerate(history[-20:]):  # 최근 20개 메시지 확인
            if msg.get("role") == "user":
                recent_user_questions.append({
                    "content": msg.get("content", "").lower(),
                    "index": i
                })
            elif msg.get("role") == "assistant" and recent_user_questions:
                # 이전 사용자 질문에 대한 답변
                recent_answers.append({
                    "question_index": recent_user_questions[-1]["index"],
                    "answer": msg.get("content", "")
                })
        
        current_question_lower = question_lower
        # 유사도 체크 (간단한 포함 관계로)
        for past_q_info in recent_user_questions:
            past_q = past_q_info["content"]
            if past_q and len(past_q) > 5:  # 너무 짧은 질문은 제외
                # 핵심 키워드 추출하여 비교
                past_keywords = set([w for w in past_q.split() if len(w) > 2])
                current_keywords = set([w for w in current_question_lower.split() if len(w) > 2])
                if past_keywords and current_keywords:
                    similarity = len(past_keywords & current_keywords) / len(past_keywords | current_keywords)
                    if similarity > 0.5:  # 50% 이상 유사하면 반복 질문으로 간주
                        is_repeated_question = True
                        # 해당 질문에 대한 이전 답변 찾기
                        for answer_info in recent_answers:
                            if answer_info["question_index"] == past_q_info["index"]:
                                previous_answer = answer_info["answer"]
                                break
                        break
        
        # 반복 질문이고 이전 답변이 있으면 API 호출 없이 재사용
        if is_repeated_question and previous_answer:
            answer = f"아, 이전에 물어보셨던 내용과 비슷하시네요! 이전 답변을 다시 드릴게요:\n\n{previous_answer}\n\n혹시 더 궁금한 점이 있으면 언제든지 물어보세요!"
            
            # 대화 히스토리 업데이트
            history.append({"role": "user", "content": payload.question})
            history.append({"role": "assistant", "content": answer})
            if len(history) > 50:
                history = history[-50:]
            _conversation_history[conversation_id] = history
            
            return ChatResponse(
                answer=answer,
                sources=[],
                conversation_id=conversation_id,
                course_id=payload.course_id,
            )
    
    # 시간 관련 질문인지 확인 (예: "지금 몇분대야", "현재 시간", "몇 분대")
    # 단순히 현재 시간만 물어보는 질문인지 확인 (이해 관련 질문 제외)
    is_time_question = False
    if payload.current_time is not None and payload.current_time > 0:
        time_keywords = ["몇분", "몇 분", "시간", "분대"]
        question_lower = payload.question.lower()
        # "이해", "설명", "다시" 같은 키워드가 없고, 시간 관련 키워드만 있는 경우
        has_understanding_keyword = any(kw in question_lower for kw in ["이해", "모르겠", "다시", "설명", "어려워", "어렵", "무엇", "뭐", "말씀", "말하는"])
        has_time_keyword = any(keyword in question_lower for keyword in time_keywords)
        # 시간 관련 키워드는 있지만 이해 관련 키워드는 없는 경우에만 시간만 알려주기
        is_time_question = has_time_keyword and not has_understanding_keyword
        
        if is_time_question:
            # 시간 관련 질문이면 직접 답변
            minutes = int(payload.current_time // 60)
            seconds = int(payload.current_time % 60)
            return ChatResponse(
                answer=f"현재 {minutes}분 {seconds}초 부분을 시청 중이시군요! 😊\n\n해당 시간대의 강의 내용에 대해 궁금한 점이 있으시면 언제든지 물어보세요.",
                sources=[],
                conversation_id=conversation_id,
                course_id=payload.course_id,
            )
    
    # "이해가 안가요", "지금 말하는 부분", "방금 말씀" 같은 질문이면 해당 시간대 transcript 우선 사용
    use_transcript_first = False
    if payload.current_time is not None and payload.current_time > 0:
        question_lower = payload.question.lower()
        
        # 시간/맥락 관련 키워드
        recent_keywords = [
            "방금", "지금", "현재", "이 부분", "여기", "지금 이", "방금 전",
            "쌤", "선생님", "설명", "말씀", "이야기", "내용", "부분", "말하", "말씀하"
        ]
        # 이해 관련 키워드
        understanding_keywords = ["이해", "모르겠", "다시", "설명", "어려워", "어렵", "무엇", "뭐", "뭔지"]
        
        has_recent_keyword = any(keyword in question_lower for keyword in recent_keywords)
        has_understanding_keyword = any(kw in question_lower for kw in understanding_keywords)
        
        # 시간/맥락 키워드가 있거나, 이해 관련 키워드와 함께 현재 시간 정보가 있는 경우
        # 특히 "지금 말하는 부분이 이해가 안가요" 같은 질문 감지
        use_transcript_first = has_recent_keyword or (has_understanding_keyword and payload.current_time > 0)
    
    try:
        # 시간대 기반 질문이면 transcript를 먼저 사용
        result = None
        if use_transcript_first:
            use_transcript = True
            answer = ""
            docs = []
            metas = []
        else:
            # RAG 쿼리 실행 (current_time 전달)
            result = pipeline.query(
                payload.question, 
                course_id=payload.course_id,
                conversation_history=history,
                current_time=payload.current_time
            )
            
            answer = result.get("answer", "")
            docs = result.get("documents", [])
            metas = result.get("metadatas", [])
            
            # 검색 결과가 없거나 페르소나만 있으면 저장된 transcript 사용
            use_transcript = False
            
            # 실제 강의 내용이 있는지 확인 (페르소나 제외)
            has_lecture_content = False
            for i, doc in enumerate(docs):
                meta = metas[i] if i < len(metas) else {}
                doc_type = meta.get("type", "")
                # 페르소나가 아니고 실제 강의 내용인 경우
                if doc_type not in ["persona", None, ""]:
                    has_lecture_content = True
                    break
            
            if not docs or len(docs) == 0:
                print(f"[CHAT DEBUG] ⚠️ No documents found in RAG search for course_id={payload.course_id}, trying transcript file...")
                use_transcript = True
            elif not has_lecture_content:
                print(f"[CHAT DEBUG] ⚠️ Only persona found, no lecture content in RAG search for course_id={payload.course_id}, trying transcript file...")
                use_transcript = True
            elif answer and ("강의 컨텍스트를 찾지 못했습니다" in answer or "No documents" in answer or "No context" in answer):
                print(f"[CHAT DEBUG] ⚠️ RAG returned empty context for course_id={payload.course_id}, trying transcript file...")
                use_transcript = True
        
        if use_transcript:
            print(f"[CHAT DEBUG] 🔍 Loading transcript for course_id={payload.course_id}, current_time={payload.current_time}")
            context_text = None  # 초기화
            try:
                transcript_data = _load_transcript_for_course(payload.course_id, session, return_segments=True)
                print(f"[CHAT DEBUG] 📄 Transcript data type: {type(transcript_data)}")
                
                if transcript_data is None:
                    print(f"[CHAT DEBUG] ❌ Transcript file not found for course_id={payload.course_id}")
                    # transcript가 없으면 기본 답변 제공
                    if use_transcript_first:
                        minutes = int(payload.current_time // 60) if payload.current_time else 0
                        seconds = int(payload.current_time % 60) if payload.current_time else 0
                        answer = (
                            f"죄송합니다. 현재 {minutes}분 {seconds}초 부분의 강의 자막 파일을 찾을 수 없습니다. "
                            f"강의가 아직 처리 중이거나 자막 파일이 준비되지 않았을 수 있습니다."
                        )
                    else:
                        answer = "죄송합니다. 강의 자막 파일을 찾을 수 없습니다. 강의가 아직 처리 중일 수 있습니다."
                else:
                    transcript_text = transcript_data.get("text", "") if isinstance(transcript_data, dict) else transcript_data or ""
                    segments = transcript_data.get("segments", []) if isinstance(transcript_data, dict) else []
                    print(f"[CHAT DEBUG] 📝 Transcript text length: {len(transcript_text)}, segments: {len(segments)}")
                    
                    if not transcript_text or not transcript_text.strip():
                        print(f"[CHAT DEBUG] ⚠️ Transcript text is empty")
                        if use_transcript_first:
                            minutes = int(payload.current_time // 60) if payload.current_time else 0
                            seconds = int(payload.current_time % 60) if payload.current_time else 0
                            answer = (
                                f"죄송합니다. 현재 {minutes}분 {seconds}초 부분의 강의 자막 내용이 비어있습니다."
                            )
                        else:
                            answer = "죄송합니다. 강의 자막 내용이 비어있습니다."
                    else:
                        # transcript_text가 있는 경우 기존 로직 실행
                        # 현재 시청 시간대의 transcript segment 찾기
                        context_text = transcript_text
                        if payload.current_time is not None and payload.current_time > 0 and segments:
                            # 현재 시간 ±60초 범위의 segment 찾기 (범위 확대)
                            time_window = 60  # ±60초
                            relevant_segments = []
                            for seg in segments:
                                start = float(seg.get("start", 0))
                                end = float(seg.get("end", 0))
                                current_time = float(payload.current_time)
                                
                                # 현재 시간이 segment 범위 내에 있거나 ±60초 이내인 경우
                                if (start <= current_time <= end) or \
                                   (abs(start - current_time) <= time_window) or \
                                   (abs(end - current_time) <= time_window):
                                    # 거리 계산 (가까운 순으로 정렬하기 위해)
                                    distance = min(abs(start - current_time), abs(end - current_time), abs((start + end) / 2 - current_time))
                                    relevant_segments.append((distance, seg))
                            
                            # 거리순으로 정렬 (가까운 것부터)
                            relevant_segments.sort(key=lambda x: x[0])
                            relevant_segments = [seg for _, seg in relevant_segments]
                            
                            # 관련 segment가 있으면 해당 부분을 우선 사용
                            if relevant_segments:
                                context_parts = []
                                # 최대 10개 segment 사용 (더 많은 컨텍스트 제공)
                                for seg in relevant_segments[:10]:
                                    seg_text = seg.get("text", "").strip()
                                    if seg_text:
                                        context_parts.append(seg_text)
                                
                                if context_parts:
                                    context_text = " ".join(context_parts)
                                    print(f"[CHAT DEBUG] 📍 Using transcript segments around {payload.current_time}s: {len(relevant_segments)} segments, {len(context_text)} chars")
                                else:
                                    # segment가 있지만 텍스트가 없으면 전체 transcript 사용
                                    context_text = transcript_text[:8000]
                                    print(f"[CHAT DEBUG] ⚠️ Segments found but no text, using full transcript")
                            else:
                                # 관련 segment가 없으면 전체 transcript 사용
                                context_text = transcript_text[:8000]
                                print(f"[CHAT DEBUG] ⚠️ No segments found around {payload.current_time}s, using full transcript")
                        else:
                            # current_time이 없으면 전체 transcript 사용
                            context_text = transcript_text[:8000]
                        
                        # context_text가 비어있으면 에러
                        if not context_text or not context_text.strip():
                            print(f"[CHAT DEBUG] ⚠️ Context text is empty after processing")
                            if use_transcript_first:
                                minutes = int(payload.current_time // 60) if payload.current_time else 0
                                seconds = int(payload.current_time % 60) if payload.current_time else 0
                                answer = (
                                    f"죄송합니다. 현재 {minutes}분 {seconds}초 부분의 강의 내용을 찾을 수 없습니다."
                                )
                            else:
                                answer = "죄송합니다. 해당 시간대의 강의 내용을 찾을 수 없습니다."
                        else:
                            # 저장된 transcript를 컨텍스트로 사용하여 다시 질의
                            from openai import OpenAI
                            from ai.config import AISettings
                            settings = AISettings()
                            
                            if settings.openai_api_key:
                                # 페르소나 프롬프트 가져오기
                                persona_prompt = ""
                                try:
                                    from ai.services.vectorstore import get_chroma_client, get_collection
                                    client = get_chroma_client(settings)
                                    collection = get_collection(client, settings)
                                    persona_results = collection.get(
                                        ids=[f"{payload.course_id}-persona"],
                                        include=["documents"],
                                    )
                                    if persona_results.get("documents") and len(persona_results["documents"]) > 0:
                                        persona_prompt = persona_results["documents"][0]
                                except Exception:
                                    pass
                                
                                # 현재 시청 시간 정보 추가
                                time_context = ""
                                current_time_info = ""
                                if payload.current_time is not None and payload.current_time > 0:
                                    minutes = int(payload.current_time // 60)
                                    seconds = int(payload.current_time % 60)
                                    time_context = f"\n\n[참고: 학생이 현재 강의의 {minutes}분 {seconds}초 부분을 시청 중입니다.]\n"
                                    current_time_info = f"현재 시청 시간: {minutes}분 {seconds}초"
                                
                                # transcript 기반 프롬프트 생성
                                system_message = (
                                    "당신은 이 강의를 가르치는 강사입니다. 학생의 질문에 답변할 때, 강사로서 자연스럽게 대화하세요. "
                                    "'여러분'이나 '학생' 같은 표현을 사용하지 말고, 직접적으로 '저는', '제가' 같은 표현을 사용하여 "
                                    "강의를 가르치는 선생님으로서 학생에게 설명하는 톤으로 답변하세요.\n\n"
                                )
                                if current_time_info:
                                    system_message += (
                                        f"**중요**: 학생이 현재 시청 중인 시간대 정보를 알고 있습니다. "
                                        f"학생이 '지금 몇분대야', '현재 시간', '몇 분대' 같은 질문을 하면 "
                                        f"현재 시청 중인 시간대를 친절하게 알려주세요.\n\n"
                                    )
                                
                                # 질문 유형에 따라 프롬프트 조정
                                is_time_based_question = use_transcript_first
                                
                                # 대화 히스토리 질문 처리 (API 호출 없이 히스토리에서 직접 답변 생성)
                                if is_history_question:
                                    # 히스토리에서 직접 요약 생성 (API 호출 없음)
                                    if history:
                                        # 최근 대화 요약
                                        recent_conversations = []
                                        for i, msg in enumerate(history[-10:]):
                                            role = msg.get("role", "")
                                            content = msg.get("content", "")
                                            if role == "user":
                                                recent_conversations.append(f"학생: {content}")
                                            elif role == "assistant":
                                                recent_conversations.append(f"챗봇: {content}")
                                        
                                        if recent_conversations:
                                            answer = "지금까지 우리가 나눈 대화 내용은 다음과 같습니다:\n\n" + "\n\n".join(recent_conversations[-6:]) + "\n\n궁금한 점이 더 있으면 언제든지 물어보세요!"
                                        else:
                                            answer = "아직 대화 내용이 없습니다. 궁금한 점이 있으면 언제든지 물어보세요!"
                                    else:
                                        answer = "아직 대화 내용이 없습니다. 궁금한 점이 있으면 언제든지 물어보세요!"
                                    
                                    # 대화 히스토리 업데이트
                                    history.append({"role": "user", "content": payload.question})
                                    history.append({"role": "assistant", "content": answer})
                                    if len(history) > 50:
                                        history = history[-50:]
                                    _conversation_history[conversation_id] = history
                                    
                                    return ChatResponse(
                                        answer=answer,
                                        sources=[],
                                        conversation_id=conversation_id,
                                        course_id=payload.course_id,
                                    )
                                elif is_time_based_question:
                                    # 학생의 질문이 이해 관련인지 확인
                                    is_understanding_question = any(kw in question_lower for kw in [
                                        "이해", "모르겠", "어려워", "어렵", "설명", "다시", "무엇", "뭐"
                                    ])
                                    
                                    if is_understanding_question:
                                        instruction = (
                                            "**중요**: 당신은 이 강의를 가르치는 강사입니다. 학생의 질문에 답변할 때, 강사로서 자연스럽게 대화하세요. "
                                            "'여러분'이나 '학생', '챗봇' 같은 표현을 사용하지 말고, 직접적으로 '저는', '제가' 같은 표현을 사용하여 "
                                            "강의를 가르치는 선생님으로서 학생에게 설명하는 톤으로 답변하세요.\n\n"
                                            "학생이 현재 시청 중인 시간대의 강의 내용을 이해하지 못해서 질문하고 있습니다. "
                                            "위에 제공된 강의 전사 내용은 학생이 현재 시청 중인 시간대(또는 그 근처)의 내용입니다. "
                                            "**반드시 해당 시간대에서 설명된 내용을 바탕으로 답변해야 합니다.** "
                                            "단순히 현재 시간만 알려주지 말고, 해당 시간대에서 실제로 설명한 내용을 더 쉽고 명확하게 설명해주세요. "
                                            "예를 들어, 학생이 '지금 말하는 부분이 이해가 안가요'라고 하면, "
                                            "해당 시간대에서 설명한 개념이나 내용을 더 쉽게 풀어서 설명하거나 예시를 들어 설명해주세요. "
                                            "답변은 친절하고 학생의 이해를 돕는 방식으로 작성하되, 답변이 너무 길어지면 적절히 나누어 설명하세요."
                                        )
                                    else:
                                        instruction = (
                                            "**중요**: 당신은 이 강의를 가르치는 강사입니다. 학생의 질문에 답변할 때, 강사로서 자연스럽게 대화하세요. "
                                            "'여러분'이나 '학생', '챗봇' 같은 표현을 사용하지 말고, 직접적으로 '저는', '제가' 같은 표현을 사용하여 "
                                            "강의를 가르치는 선생님으로서 학생에게 설명하는 톤으로 답변하세요.\n\n"
                                            "학생이 현재 시청 중인 시간대의 강의 내용에 대해 질문하고 있습니다. "
                                            "위에 제공된 강의 전사 내용은 학생이 현재 시청 중인 시간대(또는 그 근처)의 내용입니다. "
                                            "이 내용을 바탕으로 학생의 질문에 정확하고 친절하게 답변해주세요. "
                                            "답변은 명확하고 간결하게 작성하되, 답변이 너무 길어지면 적절히 나누어 설명하세요."
                                        )
                                    max_tokens_for_response = 1500
                                else:
                                    instruction = (
                                        "**중요**: 당신은 이 강의를 가르치는 강사입니다. 학생의 질문에 답변할 때, 강사로서 자연스럽게 대화하세요. "
                                        "'여러분'이나 '학생', '챗봇' 같은 표현을 사용하지 말고, 직접적으로 '저는', '제가' 같은 표현을 사용하여 "
                                        "강의를 가르치는 선생님으로서 학생에게 설명하는 톤으로 답변하세요.\n\n"
                                        "위 강의 내용을 바탕으로 질문에 답변하세요. "
                                        "강의 내용에서 직접 답을 찾을 수 있으면 그대로 사용하고, "
                                        "없으면 일반적인 지식으로 보완하되 강의 범위와 관련이 있음을 명시하세요. "
                                        "답변이 너무 길어지면 적절히 나누어 설명하세요."
                                    )
                                    max_tokens_for_response = 1500
                                
                                chat_prompt = (
                                    f"{persona_prompt}\n\n" if persona_prompt else ""
                                ) + (
                                    f"{system_message}"
                                    f"강의 전사 내용 (현재 시청 시간대):\n{context_text}\n{time_context}\n"
                                    f"학생 질문: {payload.question}\n\n"
                                    f"{instruction}"
                                )
                                
                                # 대화 히스토리 포함
                                messages = []
                                system_content = ""
                                if persona_prompt:
                                    system_content = persona_prompt
                                else:
                                    system_content = (
                                        "당신은 이 강의를 가르치는 강사입니다. 학생의 질문에 답변할 때, 강사로서 자연스럽게 대화하세요. "
                                        "'여러분'이나 '학생', '챗봇' 같은 표현을 사용하지 말고, 직접적으로 '저는', '제가' 같은 표현을 사용하여 "
                                        "강의를 가르치는 선생님으로서 학생에게 설명하는 톤으로 답변하세요."
                                    )
                                
                                # 현재 시청 시간 정보를 system message에 추가
                                if payload.current_time is not None and payload.current_time > 0:
                                    minutes = int(payload.current_time // 60)
                                    seconds = int(payload.current_time % 60)
                                    system_content += f"\n\n**중요**: 학생이 현재 강의의 {minutes}분 {seconds}초 부분을 시청 중입니다. 학생이 '지금 몇분대야', '현재 시간', '몇 분대' 같은 질문을 하면 현재 시청 중인 시간대를 친절하게 알려주세요."
                                
                                messages.append({"role": "system", "content": system_content})
                                
                                # 대화 히스토리 추가 (대화 히스토리 질문이면 더 많이 포함)
                                if history:
                                    if is_history_question:
                                        # 대화 히스토리 질문이면 최근 20개 포함
                                        recent_history = history[-20:]
                                    else:
                                        recent_history = history[-10:]  # 일반적으로 최근 10개
                                    
                                    for msg in recent_history:
                                        role = msg.get("role", "user")
                                        content = msg.get("content", "")
                                        if role in ["user", "assistant"] and content:
                                            messages.append({"role": role, "content": content})
                                
                                # 대화 히스토리 질문이면 히스토리 정보를 프롬프트에 명시
                                if is_history_question:
                                    chat_prompt = (
                                        f"학생이 '{payload.question}'라고 질문했습니다. "
                                        f"위 대화 히스토리를 참고하여 학생과 챗봇이 지금까지 어떤 대화를 나눴는지 요약해서 알려주세요. "
                                        f"간결하고 명확하게 답변하세요."
                                    )
                                else:
                                    messages.append({"role": "user", "content": chat_prompt})
                                
                                try:
                                    client = OpenAI(api_key=settings.openai_api_key)
                                    resp = client.chat.completions.create(
                                        model=settings.llm_model,
                                        messages=messages,
                                        temperature=0.3,
                                        max_tokens=max_tokens_for_response if 'max_tokens_for_response' in locals() else 1500,
                                    )
                                    answer = resp.choices[0].message.content
                                    
                                    # 답변이 너무 길 경우 강력하게 나누기 (항상 빈 줄로 구분)
                                    if answer and len(answer) > 250:  # 250자 이상이면 나누기 (더 적극적으로)
                                        # 먼저 빈 줄로 구분된 문단으로 나누기
                                        paragraphs = answer.split('\n\n')
                                        
                                        if len(paragraphs) > 1:
                                            # 문단이 여러 개면 각 문단을 검사하여 적절히 나누기
                                            divided_parts = []
                                            for para in paragraphs:
                                                para = para.strip()
                                                if not para:
                                                    continue
                                                
                                                # 문단이 250자 이상이면 문장 단위로 더 나누기
                                                if len(para) > 250:
                                                    # 마침표, 느낌표, 물음표로 문장 나누기
                                                    sentences = []
                                                    current_sentence = ""
                                                    for char in para:
                                                        current_sentence += char
                                                        if char in ['。', '.', '!', '?'] and len(current_sentence.strip()) > 10:
                                                            # 문장이 최소 10자 이상일 때만 나누기
                                                            sentences.append(current_sentence.strip())
                                                            current_sentence = ""
                                                    if current_sentence.strip():
                                                        sentences.append(current_sentence.strip())
                                                    
                                                    # 문장들을 적절히 묶어서 250자 이하로 만들기
                                                    current_chunk = ""
                                                    for sent in sentences:
                                                        if len(current_chunk) + len(sent) + 1 < 250:
                                                            current_chunk += (sent + " " if current_chunk else sent)
                                                        else:
                                                            if current_chunk:
                                                                divided_parts.append(current_chunk.strip())
                                                            current_chunk = sent + " "
                                                    if current_chunk:
                                                        divided_parts.append(current_chunk.strip())
                                                else:
                                                    divided_parts.append(para)
                                            
                                            if len(divided_parts) > 1:
                                                answer = '\n\n'.join(divided_parts)
                                        else:
                                            # 문단이 하나면 문장 단위로 나누기 (더 적극적으로)
                                            # 마침표, 느낌표, 물음표로 문장 나누기
                                            sentences = []
                                            current_sentence = ""
                                            for char in answer:
                                                current_sentence += char
                                                if char in ['。', '.', '!', '?'] and len(current_sentence.strip()) > 10:
                                                    sentences.append(current_sentence.strip())
                                                    current_sentence = ""
                                            if current_sentence.strip():
                                                sentences.append(current_sentence.strip())
                                            
                                            # 문장들을 적절히 묶어서 250자 이하로 만들기
                                            divided_parts = []
                                            current_chunk = ""
                                            for sent in sentences:
                                                if len(current_chunk) + len(sent) + 1 < 250:
                                                    current_chunk += (sent + " " if current_chunk else sent)
                                                else:
                                                    if current_chunk:
                                                        divided_parts.append(current_chunk.strip())
                                                    current_chunk = sent + " "
                                            if current_chunk:
                                                divided_parts.append(current_chunk.strip())
                                            
                                            if len(divided_parts) > 1:
                                                answer = '\n\n'.join(divided_parts)
                                    if not answer or not answer.strip():
                                        raise ValueError("Empty response from OpenAI")
                                    print(f"[CHAT DEBUG] ✅ Used transcript file for course_id={payload.course_id}, answer length: {len(answer)}")
                                except Exception as e:
                                    import traceback
                                    error_msg = str(e)
                                    print(f"[CHAT DEBUG] ❌ Failed to use transcript: {error_msg}")
                                    print(f"[CHAT DEBUG] Traceback: {traceback.format_exc()}")
                                    # 에러 발생 시 기본 답변 제공
                                    if use_transcript_first:
                                        # 시간 기반 질문인데 실패한 경우
                                        minutes = int(payload.current_time // 60) if payload.current_time else 0
                                        seconds = int(payload.current_time % 60) if payload.current_time else 0
                                        answer = (
                                            f"죄송합니다. 현재 {minutes}분 {seconds}초 부분의 강의 내용을 불러오는 중 문제가 발생했습니다. "
                                            f"잠시 후 다시 질문해주시거나, 다른 질문을 해주세요."
                                        )
                                    else:
                                        # 일반 질문인데 실패한 경우
                                        answer = "죄송합니다. 답변을 생성하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
                            else:
                                # OPENAI_API_KEY가 없는 경우
                                answer = "죄송합니다. OpenAI API 키가 설정되지 않았습니다."
            except Exception as e:
                import traceback
                error_msg = str(e)
                print(f"[CHAT DEBUG] ❌ Exception in transcript loading: {error_msg}")
                print(f"[CHAT DEBUG] Traceback: {traceback.format_exc()}")
                # 예외 발생 시 기본 답변 제공
                if use_transcript_first:
                    minutes = int(payload.current_time // 60) if payload.current_time else 0
                    seconds = int(payload.current_time % 60) if payload.current_time else 0
                    answer = (
                        f"죄송합니다. 현재 {minutes}분 {seconds}초 부분의 강의 내용을 불러오는 중 오류가 발생했습니다. "
                        f"잠시 후 다시 질문해주세요."
                    )
                else:
                    answer = "죄송합니다. 강의 내용을 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        
        # answer가 비어있으면 기본 답변 제공
        if not answer or not answer.strip():
            print(f"[CHAT DEBUG] ⚠️ Answer is empty, providing default response")
            if use_transcript_first and payload.current_time:
                minutes = int(payload.current_time // 60)
                seconds = int(payload.current_time % 60)
                answer = (
                    f"죄송합니다. 현재 {minutes}분 {seconds}초 부분에 대한 답변을 생성할 수 없었습니다. "
                    f"다시 질문해주시거나 다른 질문을 해주세요."
                )
            else:
                answer = "죄송합니다. 답변을 생성할 수 없었습니다. 다시 질문해주세요."
        
        # 대화 히스토리에 현재 질문과 답변 추가
        history.append({"role": "user", "content": payload.question})
        history.append({"role": "assistant", "content": answer})
        # 최대 20개 대화만 유지 (메모리 절약)
        if len(history) > 20:
            history = history[-20:]
        _conversation_history[conversation_id] = history
        
        # sources 설정 (result가 있을 때만)
        sources = []
        if result is not None:
            sources = [str(src) for src in result.get("documents", [])]
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            conversation_id=conversation_id,
            course_id=payload.course_id,
        )
    except Exception as e:
        error_msg = str(e)
        # OpenAI 할당량 에러 처리
        if "할당량" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg:
            answer = "⚠️ OpenAI API 할당량이 초과되었습니다. OpenAI 계정의 크레딧을 확인하거나 결제 정보를 업데이트하세요. https://platform.openai.com/account/billing"
        else:
            answer = f"⚠️ 오류 발생: {error_msg}"
        
        return ChatResponse(
            answer=answer,
            sources=[],
            conversation_id=conversation_id,
            course_id=payload.course_id,
        )


@router.post("/summary", response_model=SummaryResponse)
def generate_summary(
    payload: SummaryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
    session: Session = Depends(get_session),
) -> SummaryResponse:
    """
    강의 요약노트 생성 (저장된 STT 결과물 사용)
    """
    # answer 변수 초기화
    answer = ""
    key_points = []  # key_points 초기화
    
    # 저장된 transcript 파일 찾기
    transcript_text = _load_transcript_for_course(payload.course_id, session)
    
    if transcript_text:
        # 저장된 STT 결과물을 직접 사용
        summary_prompt = (
            f"다음은 강의 전사 내용입니다. 이 강의의 핵심 내용을 **마크다운 형식**으로 전문적이고 시각적으로 잘 정리된 요약노트를 작성해주세요.\n\n"
            f"## 강의 전사 내용:\n{transcript_text}\n\n"
            f"## 중요 안내사항:\n"
            f"- 이 전사 내용은 자동 음성 인식(STT)으로 생성되었으므로, 일부 단어가 부정확하거나 오타가 있을 수 있습니다.\n"
            f"- 문맥을 고려하여 의도된 단어나 개념을 추론하고, 자연스럽고 정확한 표현으로 수정해주세요.\n"
            f"- 의미가 불분명한 부분은 주변 문맥을 바탕으로 가장 합리적인 해석을 적용해주세요.\n"
            f"- 전문 용어나 고유명사가 잘못 인식된 경우, 강의 주제와 맥락에 맞게 올바르게 수정해주세요.\n\n"
            f"## 요약노트 작성 지침:\n\n"
            f"다음 구조와 형식을 **정확히** 따라주세요:\n\n"
            f"### 1. 강의 개요 (## 강의 개요)\n"
            f"- 2-3문단으로 전체 강의 내용을 요약\n"
            f"- **굵은 글씨**로 핵심 키워드 강조\n"
            f"- 명확하고 간결한 문장 사용\n\n"
            f"### 2. 핵심 개념 정리 (## 핵심 개념)\n"
            f"- 주요 개념들을 **표 형식**으로 정리\n"
            f"- 표 헤더: | 개념 | 설명 | 예시/비고 |\n"
            f"- 각 개념을 한 줄씩 표로 작성\n"
            f"- 예시:\n"
            f"  | 세포 분열 | 세포가 분열하여 새로운 세포를 만드는 과정 | 유사 분열, 감수 분열 |\n\n"
            f"### 3. 주요 포인트 (## 주요 포인트)\n"
            f"- 불릿 포인트로 나열 (최대 10개)\n"
            f"- 각 포인트는 한 문장으로 간결하게\n"
            f"- 중요한 내용은 **굵은 글씨**로 강조\n"
            f"- 형식: `- **핵심 키워드**: 설명 내용`\n\n"
            f"### 4. 학습 체크리스트 (## 학습 체크리스트)\n"
            f"- 학습자가 확인해야 할 내용을 체크리스트 형식으로\n"
            f"- 형식: `- [ ] 확인할 내용`\n\n"
            f"**주의사항:**\n"
            f"- 반드시 마크다운 문법을 정확히 사용해주세요\n"
            f"- 표는 반드시 `|` 기호로 구분하고 헤더와 구분선을 포함해주세요\n"
            f"- 섹션은 `##` (H2)로 시작하고, 하위 섹션은 `###` (H3)를 사용해주세요\n"
            f"- 강조는 `**텍스트**` 형식을 사용해주세요\n"
            f"- 불필요한 설명 없이 핵심만 간결하게 작성해주세요\n"
            f"- **중요: 각 섹션(강의 개요, 핵심 개념, 주요 포인트)에 동일한 내용을 반복하지 마세요. 각 섹션은 서로 다른 관점과 정보를 제공해야 합니다.**\n"
            f"- 핵심 개념 정리는 표 형식으로 구체적인 개념과 설명을, 주요 포인트는 불릿 포인트로 핵심 요약을 제공하세요.\n"
            f"- 모든 내용은 강의 전사 내용을 기반으로 정확하게 작성해주세요"
        )
        
        # LLM에 직접 전달 (RAG 검색 없이)
        from openai import OpenAI
        from ai.config import AISettings
        settings = AISettings()
        
        if not settings.openai_api_key:
            answer = "⚠️ OPENAI_API_KEY가 설정되지 않았습니다."
        else:
            client = OpenAI(api_key=settings.openai_api_key)
            try:
                resp = client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 교육 전문가이자 학습 자료 작성 전문가입니다. 강의 내용을 분석하여 시각적으로 잘 정리된 마크다운 형식의 요약노트를 작성합니다. 표, 섹션 구분, 강조를 적절히 활용하여 학습자가 쉽게 이해하고 복습할 수 있도록 구조화된 요약을 제공합니다."
                        },
                        {"role": "user", "content": summary_prompt}
                    ],
                    temperature=0.2,  # 더 일관된 형식 유지
                )
                answer = resp.choices[0].message.content or ""
                
                # LLM이 마크다운을 코드 블록으로 감싼 경우 제거
                if answer and answer.strip():
                    try:
                        # ```markdown ... ``` 제거
                        if answer.strip().startswith("```markdown"):
                            answer = answer.strip()
                            if answer.startswith("```markdown"):
                                answer = answer.replace("```markdown", "", 1)
                            if answer.endswith("```"):
                                answer = answer.rsplit("```", 1)[0]
                            answer = answer.strip()
                        # <pre><code class="language-markdown"> ... </code></pre> 제거
                        elif "<pre><code class=\"language-markdown\">" in answer or "<pre><code class='language-markdown'>" in answer:
                            answer = re.sub(r'<pre><code class=["\']language-markdown["\']>', '', answer, flags=re.IGNORECASE)
                            answer = re.sub(r'</code></pre>', '', answer, flags=re.IGNORECASE)
                            answer = answer.strip()
                    except Exception as clean_error:
                        print(f"⚠️ 코드 블록 제거 중 오류 (무시하고 계속): {clean_error}")
                        # 오류 발생 시 원본 유지
                
                # 주요 포인트 추출 (HTML 변환 전에 수행)
                key_points = []
                if answer and answer.strip():
                    lines = answer.split("\n")
                    for line in lines:
                        line = line.strip()
                        # 불릿 포인트 또는 번호 목록 패턴
                        if line.startswith(("•", "-", "·", "*")) or re.match(r"^\d+[\.\)]\s+", line):
                            point = line.lstrip("•-·*").strip()
                            point = re.sub(r"^\d+[\.\)]\s*", "", point).strip()  # 번호 제거
                            # HTML 태그 제거 (마크다운 형식이므로 ** 등은 유지)
                            point = re.sub(r'<[^>]+>', '', point)  # HTML 태그 제거
                            if point and len(point) > 10:  # 너무 짧은 것은 제외
                                key_points.append(point)
                        elif line.startswith("- ") or line.startswith("• "):
                            point = line[2:].strip()
                            point = re.sub(r'<[^>]+>', '', point)  # HTML 태그 제거
                            if point and len(point) > 10:
                                key_points.append(point)
                
                # 마크다운을 HTML로 변환 (선택적 - 실패해도 프론트엔드에서 처리)
                if answer and answer.strip():
                    try:
                        import markdown
                        print(f"📝 원본 마크다운 길이: {len(answer)}")
                        print(f"📝 원본 마크다운 샘플: {answer[:200]}")
                        
                        # 확장 기능을 안전하게 로드
                        try:
                            md = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists'])
                        except Exception as ext_error:
                            print(f"⚠️ 확장 기능 로드 실패, 기본 마크다운 사용: {ext_error}")
                            md = markdown.Markdown()
                        
                        answer = md.convert(answer)
                        print(f"✅ HTML 변환 완료, 길이: {len(answer)}")
                        print(f"✅ HTML 샘플: {answer[:200]}")
                    except ImportError:
                        # markdown 모듈이 없으면 원본 텍스트 유지 (프론트엔드에서 처리)
                        print("ℹ️ markdown 모듈이 없습니다. 프론트엔드에서 변환합니다.")
                    except Exception as md_error:
                        import traceback
                        print(f"⚠️ Markdown 변환 오류 (프론트엔드에서 처리): {md_error}")
                        # 변환 실패 시 원본 텍스트 유지 (프론트엔드에서 처리)
                
                # 주요 포인트 추출 (HTML 변환 후에도 HTML 태그 제거)
                if not key_points:  # 아직 추출하지 않았으면
                    key_points = []
                    # HTML에서 텍스트만 추출
                    # HTML 태그 제거
                    text_only = re.sub(r'<[^>]+>', '', answer)
                    lines = text_only.split("\n")
                    for line in lines:
                        line = line.strip()
                        # 불릿 포인트 또는 번호 목록 패턴
                        if line.startswith(("•", "-", "·", "*")) or re.match(r"^\d+[\.\)]\s+", line):
                            point = line.lstrip("•-·*").strip()
                            point = re.sub(r"^\d+[\.\)]\s*", "", point).strip()
                            if point and len(point) > 10:
                                key_points.append(point)
                        elif line.startswith("- ") or line.startswith("• "):
                            point = line[2:].strip()
                            if point and len(point) > 10:
                                key_points.append(point)
                
                # key_points에서 HTML 태그 제거
                key_points = [re.sub(r'<[^>]+>', '', point).strip() for point in key_points if point]
                
            except Exception as e:
                import traceback
                print(f"❌ Summary generation error: {e}")
                print(traceback.format_exc())
                answer = f"⚠️ 요약 생성 중 오류 발생: {str(e)}"
                key_points = []
    else:
        # transcript 파일이 없으면 기존 방식 (RAG 검색) 사용
        summary_prompt = (
            "이 강의의 핵심 내용을 **마크다운 형식**으로 전문적이고 시각적으로 잘 정리된 요약노트를 작성해주세요.\n\n"
            "## 요약노트 작성 지침:\n\n"
            "다음 구조와 형식을 **정확히** 따라주세요:\n\n"
            "### 1. 강의 개요 (## 강의 개요)\n"
            "- 2-3문단으로 전체 강의 내용을 요약\n"
            "- **굵은 글씨**로 핵심 키워드 강조\n\n"
            "### 2. 핵심 개념 정리 (## 핵심 개념)\n"
            "- 주요 개념들을 **표 형식**으로 정리\n"
            "- 표 헤더: | 개념 | 설명 | 예시/비고 |\n\n"
            "### 3. 주요 포인트 (## 주요 포인트)\n"
            "- 불릿 포인트로 나열 (최대 10개)\n"
            "- 형식: `- **핵심 키워드**: 설명 내용`\n\n"
            "### 4. 학습 체크리스트 (## 학습 체크리스트)\n"
            "- 학습자가 확인해야 할 내용을 체크리스트 형식으로\n\n"
            "**주의사항:**\n"
            "- 반드시 마크다운 문법을 정확히 사용해주세요\n"
            "- 표는 반드시 `|` 기호로 구분하고 헤더와 구분선을 포함해주세요\n"
            "- **중요: 각 섹션(강의 개요, 핵심 개념, 주요 포인트)에 동일한 내용을 반복하지 마세요. 각 섹션은 서로 다른 관점과 정보를 제공해야 합니다.**\n"
            "- 핵심 개념 정리는 표 형식으로 구체적인 개념과 설명을, 주요 포인트는 불릿 포인트로 핵심 요약을 제공하세요."
        )
        
        try:
            result = pipeline.query(
                summary_prompt,
                course_id=payload.course_id,
                k=8,  # 더 많은 컨텍스트 가져오기
            )
            answer = result.get("answer", "") or ""
            
            # 마크다운을 HTML로 변환 (선택적 - 실패해도 프론트엔드에서 처리)
            if answer and answer.strip():
                try:
                    import markdown
                    print(f"📝 원본 마크다운 길이: {len(answer)}")
                    print(f"📝 원본 마크다운 샘플: {answer[:200]}")
                    
                    # 확장 기능을 안전하게 로드
                    try:
                        md = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists'])
                    except Exception as ext_error:
                        print(f"⚠️ 확장 기능 로드 실패, 기본 마크다운 사용: {ext_error}")
                        md = markdown.Markdown()
                    
                    answer = md.convert(answer)
                    print(f"✅ HTML 변환 완료, 길이: {len(answer)}")
                    print(f"✅ HTML 샘플: {answer[:200]}")
                except ImportError:
                    # markdown 모듈이 없으면 원본 텍스트 유지 (프론트엔드에서 처리)
                    print("ℹ️ markdown 모듈이 없습니다. 프론트엔드에서 변환합니다.")
                except Exception as md_error:
                    import traceback
                    print(f"⚠️ Markdown 변환 오류 (프론트엔드에서 처리): {md_error}")
                    # 변환 실패 시 원본 텍스트 유지 (프론트엔드에서 처리)
        except Exception as e:
            import traceback
            print(f"❌ RAG query error: {e}")
            print(traceback.format_exc())
            answer = f"⚠️ 요약 생성 중 오류 발생: {str(e)}"
    
    # answer가 비어있으면 기본 메시지
    if not answer or not answer.strip():
        answer = "⚠️ 요약을 생성할 수 없습니다. STT 전사 결과가 없거나 처리 중 오류가 발생했습니다."
    
    # key_points가 아직 설정되지 않았으면 추출 시도
    if not key_points:
        # HTML 태그 제거 후 텍스트만 추출
        text_only = re.sub(r'<[^>]+>', '', answer)
        lines = text_only.split("\n")
        for line in lines:
            line = line.strip()
            # 불릿 포인트 또는 번호 목록 패턴
            if line.startswith(("•", "-", "·", "*")) or re.match(r"^\d+[\.\)]\s+", line):
                point = line.lstrip("•-·*").strip()
                point = re.sub(r"^\d+[\.\)]\s*", "", point).strip()  # 번호 제거
                if point and len(point) > 10:  # 너무 짧은 것은 제외
                    key_points.append(point)
            elif line.startswith("- ") or line.startswith("• "):
                point = line[2:].strip()
                if point and len(point) > 10:
                    key_points.append(point)
        
        # 주요 포인트가 없으면 전체 요약에서 추출 시도
        if not key_points:
            # 문장 단위로 나누고 중요한 문장 추출
            sentences = text_only.replace(". ", ".\n").split("\n")
            key_points = [s.strip() for s in sentences if len(s.strip()) > 20][:10]
        
        # HTML 태그 제거
        key_points = [re.sub(r'<[^>]+>', '', point).strip() for point in key_points if point]
    
    return SummaryResponse(
        course_id=payload.course_id,
        summary=answer,
        key_points=key_points[:10],  # 최대 10개
    )


@router.post("/quiz/generate", response_model=QuizResponse)
def generate_quiz(
    payload: QuizRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
    session: Session = Depends(get_session),
) -> QuizResponse:
    """
    강의 기반 퀴즈 생성 (저장된 STT 결과물 사용)
    """
    num_questions = min(max(payload.num_questions, 1), 10)  # 1-10개 제한
    
    # 저장된 transcript 파일 찾기
    transcript_text = _load_transcript_for_course(payload.course_id, session)
    
    if transcript_text:
        # 저장된 STT 결과물을 직접 사용
        quiz_prompt = (
            f"다음은 강의 전사 내용입니다. 이 강의 내용을 바탕으로 객관식 퀴즈 {num_questions}문제를 만들어주세요.\n\n"
            f"## 강의 전사 내용:\n{transcript_text}\n\n"
            f"## 중요 안내사항:\n"
            f"- 이 전사 내용은 자동 음성 인식(STT)으로 생성되었으므로, 일부 단어가 부정확하거나 오타가 있을 수 있습니다.\n"
            f"- 문맥을 고려하여 의도된 단어나 개념을 추론하고, 자연스럽고 정확한 표현으로 수정해주세요.\n"
            f"- 의미가 불분명한 부분은 주변 문맥을 바탕으로 가장 합리적인 해석을 적용해주세요.\n"
            f"- 전문 용어나 고유명사가 잘못 인식된 경우, 강의 주제와 맥락에 맞게 올바르게 수정해주세요.\n\n"
            f"각 문제마다 다음 형식으로 작성해주세요:\n"
            f"문제1: [문제 내용]\n"
            f"A. [선택지1]\n"
            f"B. [선택지2]\n"
            f"C. [선택지3]\n"
            f"D. [선택지4]\n"
            f"정답: A (또는 B, C, D)\n\n"
            f"이런 형식으로 {num_questions}문제 만들어주세요."
        )
        
        # LLM에 직접 전달 (RAG 검색 없이)
        from openai import OpenAI
        from ai.config import AISettings
        settings = AISettings()
        
        if not settings.openai_api_key:
            answer = "⚠️ OPENAI_API_KEY가 설정되지 않았습니다."
        else:
            client = OpenAI(api_key=settings.openai_api_key)
            try:
                resp = client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 교육 전문가입니다. 강의 내용을 바탕으로 적절한 난이도의 객관식 퀴즈를 만듭니다."
                        },
                        {"role": "user", "content": quiz_prompt}
                    ],
                    temperature=0.5,  # 퀴즈는 약간 더 창의적
                )
                answer = resp.choices[0].message.content
            except Exception as e:
                answer = f"⚠️ 퀴즈 생성 중 오류 발생: {str(e)}"
    else:
        # transcript 파일이 없으면 기존 방식 (RAG 검색) 사용
        quiz_prompt = (
            f"이 강의 내용을 바탕으로 객관식 퀴즈 {num_questions}문제를 만들어주세요.\n\n"
            "## 중요 안내사항:\n"
            "- 제공된 강의 내용은 자동 음성 인식(STT)으로 생성되었을 수 있으므로, 일부 단어가 부정확하거나 오타가 있을 수 있습니다.\n"
            "- 문맥을 고려하여 의도된 단어나 개념을 추론하고, 자연스럽고 정확한 표현으로 수정해주세요.\n"
            "- 의미가 불분명한 부분은 주변 문맥을 바탕으로 가장 합리적인 해석을 적용해주세요.\n\n"
            "각 문제마다 다음 형식으로 작성해주세요:\n"
            "문제1: [문제 내용]\n"
            "A. [선택지1]\n"
            "B. [선택지2]\n"
            "C. [선택지3]\n"
            "D. [선택지4]\n"
            "정답: A (또는 B, C, D)\n\n"
            "이런 형식으로 {num_questions}문제 만들어주세요."
        )
        
        result = pipeline.query(
            quiz_prompt,
            course_id=payload.course_id,
            k=8,  # 더 많은 컨텐스트 가져오기
        )
        
        answer = result.get("answer", "")
    
    # 퀴즈 파싱
    questions = _parse_quiz_from_text(answer, num_questions)
    
    return QuizResponse(
        course_id=payload.course_id,
        questions=questions,
        quiz_id=f"quiz-{payload.course_id}-{int(__import__('time').time())}",
    )


def _load_transcript_for_course(course_id: str, session: Session, return_segments: bool = False) -> Optional[str] | Optional[dict]:
    """
    course_id에 해당하는 저장된 transcript 파일을 로드합니다.
    
    Args:
        course_id: 강의 ID
        session: DB 세션
        return_segments: True면 segments도 포함한 dict 반환, False면 텍스트만 반환
    
    Returns:
        transcript 텍스트 또는 dict (text, segments 포함) 또는 None (파일이 없을 경우)
    """
    from pathlib import Path
    import json
    from sqlmodel import select
    from core.models import Video, Course
    
    try:
        # Course 정보 가져오기
        course = session.get(Course, course_id)
        if not course:
            print(f"[TRANSCRIPT DEBUG] Course not found: {course_id}")
            return None
        
        # Video 레코드에서 transcript_path 찾기
        videos = session.exec(
            select(Video).where(
                Video.course_id == course_id,
                Video.transcript_path.isnot(None)  # transcript_path가 있는 것만
            )
        ).all()
        
        transcript_path = None
        if not videos:
            print(f"[TRANSCRIPT DEBUG] No videos with transcript_path found for course_id={course_id}")
            # DB에 없어도 파일 시스템에서 직접 찾기 시도
            try:
                from core.config import AppSettings
                app_settings = AppSettings()
                
                # 여러 가능한 instructor_id 경로 시도
                possible_instructor_ids = []
                # 일반적인 패턴을 먼저 시도 (test-instructor-1이 가장 일반적)
                possible_instructor_ids.extend([
                    "test-instructor-1",
                    "test-instructor",
                ])
                # course_id에서 추론 (test-course-1 -> test-instructor-1)
                if "-" in course_id:
                    base_name = course_id.split("-")[0]
                    possible_instructor_ids.append(f"{base_name}-instructor-1")
                    possible_instructor_ids.append(f"{base_name}-instructor")
                # DB의 instructor_id도 시도 (마지막에 추가)
                if course and course.instructor_id:
                    possible_instructor_ids.append(course.instructor_id)
                
                # 중복 제거 및 None 제거
                possible_instructor_ids = list(dict.fromkeys([pid for pid in possible_instructor_ids if pid]))
                
                print(f"[TRANSCRIPT DEBUG] Trying to find transcript files with possible instructor_ids: {possible_instructor_ids}")
                
                for instructor_id in possible_instructor_ids:
                    if not instructor_id:
                        continue
                    course_dir = app_settings.uploads_dir / instructor_id / course_id
                    print(f"[TRANSCRIPT DEBUG] Trying path: {course_dir}")
                    
                    if course_dir.exists():
                        # transcript_*.json 파일 찾기
                        transcript_files = list(course_dir.glob("transcript_*.json"))
                        if transcript_files:
                            transcript_path = transcript_files[0]
                            print(f"[TRANSCRIPT DEBUG] ✅ Found transcript file in filesystem: {transcript_path}")
                            break
                        else:
                            print(f"[TRANSCRIPT DEBUG] No transcript files found in {course_dir}")
                    else:
                        print(f"[TRANSCRIPT DEBUG] Directory does not exist: {course_dir}")
                
                if not transcript_path:
                    print(f"[TRANSCRIPT DEBUG] ❌ Could not find transcript file in any of the tried paths")
                    return None
            except Exception as e:
                print(f"[TRANSCRIPT DEBUG] Error searching filesystem: {e}")
                import traceback
                print(f"[TRANSCRIPT DEBUG] Traceback: {traceback.format_exc()}")
                return None
        else:
            # 첫 번째 transcript 파일 로드
            transcript_path_str = videos[0].transcript_path
            if not transcript_path_str:
                return None
            transcript_path = Path(transcript_path_str)
        
        if not transcript_path.exists():
            print(f"[TRANSCRIPT DEBUG] Transcript file does not exist: {transcript_path}")
            return None
        
        print(f"[TRANSCRIPT DEBUG] Loading transcript from: {transcript_path}")
        with transcript_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        transcript_text = data.get("text", "")
        
        # placeholder 체크
        if "placeholder" in transcript_text.lower():
            print(f"[TRANSCRIPT DEBUG] ⚠️ Transcript file contains placeholder text, skipping")
            return None
        
        if transcript_text and len(transcript_text.strip()) > 0:
            print(f"✅ Loaded transcript from file for course {course_id}: {transcript_path} (length: {len(transcript_text)})")
            if return_segments:
                return {
                    "text": transcript_text,
                    "segments": data.get("segments", [])
                }
            return transcript_text
        
        print(f"[TRANSCRIPT DEBUG] Transcript text is empty")
        return None
    except Exception as e:
        import traceback
        print(f"⚠️ Failed to load transcript for course {course_id}: {e}")
        print(f"[TRANSCRIPT DEBUG] Traceback: {traceback.format_exc()}")
        return None


def _parse_quiz_from_text(text: str, num_questions: int) -> list:
    """
    LLM 응답 텍스트에서 퀴즈 문제 파싱
    """
    from api.schemas import QuizQuestion
    import re
    
    questions = []
    lines = text.split("\n")
    
    current_question = None
    question_id = 1
    
    for line in lines:
        line = line.strip()
        
        # 문제 시작 패턴
        if re.match(r"^문제\s*\d+[:：]?", line, re.IGNORECASE) or re.match(r"^\d+[\.\)]\s*", line):
            if current_question and current_question.get("options"):
                # 이전 문제 저장
                questions.append(QuizQuestion(**current_question))
            
            # 새 문제 시작
            question_text = re.sub(r"^문제\s*\d+[:：]?\s*", "", line, flags=re.IGNORECASE)
            question_text = re.sub(r"^\d+[\.\)]\s*", "", question_text)
            
            current_question = {
                "id": question_id,
                "question": question_text,
                "options": [],
                "correct_answer": 0,
            }
            question_id += 1
        
        # 선택지 패턴 (A. B. C. D. 또는 A) B) C) D))
        elif re.match(r"^[A-D][\.\)]\s+", line, re.IGNORECASE):
            if current_question:
                option_text = re.sub(r"^[A-D][\.\)]\s+", "", line, flags=re.IGNORECASE)
                current_question["options"].append(option_text)
        
        # 정답 패턴
        elif re.search(r"정답[:：]?\s*([A-D])", line, re.IGNORECASE):
            if current_question:
                match = re.search(r"정답[:：]?\s*([A-D])", line, re.IGNORECASE)
                if match:
                    answer_letter = match.group(1).upper()
                    current_question["correct_answer"] = ord(answer_letter) - ord("A")
        
        # 문제 내용에 추가 (선택지가 없을 때)
        elif line and current_question and len(current_question["options"]) == 0:
            if current_question["question"]:
                current_question["question"] += " " + line
            else:
                current_question["question"] = line
    
    # 마지막 문제 저장
    if current_question and current_question.get("options") and len(current_question["options"]) >= 2:
        # 선택지가 4개가 아니면 채우기
        while len(current_question["options"]) < 4:
            current_question["options"].append(f"선택지 {len(current_question['options']) + 1}")
        questions.append(QuizQuestion(**current_question))
    
    # 최대 개수 제한
    return questions[:num_questions]


@router.post("/quiz/submit", response_model=QuizResult)
def submit_quiz(
    payload: QuizSubmitRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> QuizResult:
    """
    퀴즈 답변 제출 및 채점
    """
    # 프론트엔드에서 보낸 퀴즈 데이터 사용 (재생성하지 않음)
    if payload.questions:
        # 프론트엔드에서 퀴즈 데이터를 보낸 경우
        questions = payload.questions
    else:
        # 하위 호환성: 퀴즈 데이터가 없으면 재생성 (권장하지 않음)
        quiz_request = QuizRequest(course_id=payload.course_id, num_questions=5)
        quiz_response = generate_quiz(quiz_request, pipeline)
        questions = quiz_response.questions
    
    correct_answers = []
    wrong_answers = []
    
    # 모든 문제에 대해 채점
    for question in questions:
        question_id = question.get("id") if isinstance(question, dict) else question.id
        correct_answer = question.get("correct_answer") if isinstance(question, dict) else question.correct_answer
        
        user_answer = payload.answers.get(question_id)
        if user_answer is not None:
            if user_answer == correct_answer:
                correct_answers.append(question_id)
            else:
                wrong_answers.append(question_id)
        else:
            # 답변하지 않은 문제도 오답으로 처리
            wrong_answers.append(question_id)
    
    total = len(questions)
    score = len(correct_answers)
    percentage = round((score / total * 100) if total > 0 else 0, 1)
    
    return QuizResult(
        course_id=payload.course_id,
        score=score,
        total=total,
        percentage=percentage,
        correct_answers=correct_answers,
        wrong_answers=wrong_answers,
    )

