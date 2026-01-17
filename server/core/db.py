from typing import Generator
from pathlib import Path
from urllib.parse import urlparse

from sqlmodel import Session, SQLModel, create_engine

from core.config import AppSettings

# server 폴더 기준 경로
SERVER_ROOT = Path(__file__).resolve().parent.parent


def _prepare_sqlite_url(url: str) -> str:
    """Ensure sqlite file path exists and is absolute, fallback to server data/ if permission denied."""
    if not url.startswith("sqlite"):
        return url

    parsed = urlparse(url)
    path = parsed.path
    
    # sqlite:/// 경로 처리
    if path.startswith("///"):
        # sqlite:///./data/yeopgang.db -> ./data/yeopgang.db
        file_path = Path(path[3:])
    elif path.startswith("/"):
        # sqlite:///data/yeopgang.db -> data/yeopgang.db (절대 경로로 오해하지 않도록)
        if path.startswith("//"):
            file_path = Path(path[2:])
        else:
            file_path = Path(path[1:])
    else:
        file_path = Path(path)
    
    # 상대 경로 처리 (./data/yeopgang.db -> server/data/yeopgang.db)
    if not file_path.is_absolute():
        # ./data/yeopgang.db -> data/yeopgang.db로 정규화
        if file_path.parts and file_path.parts[0] == ".":
            file_path = Path(*file_path.parts[1:])
        # server 폴더 기준으로 해석
        file_path = SERVER_ROOT / file_path

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        # Read-only or permission-denied: fallback to server data directory
        fallback = SERVER_ROOT / "data" / file_path.name
        fallback.parent.mkdir(parents=True, exist_ok=True)
        file_path = fallback

    return f"sqlite:///{file_path}"


settings = AppSettings()
engine = create_engine(_prepare_sqlite_url(settings.database_url), echo=False, future=True)


def _migrate_add_progress_column() -> None:
    """Course 테이블에 progress 컬럼 추가 (마이그레이션)"""
    try:
        from sqlalchemy import inspect, text
        
        # SQLite인지 확인
        if engine.dialect.name != "sqlite":
            return
        
        # 테이블이 존재하는지 확인
        inspector = inspect(engine)
        if "course" not in inspector.get_table_names():
            return
        
        # progress 컬럼이 이미 있는지 확인
        columns = [col["name"] for col in inspector.get_columns("course")]
        if "progress" in columns:
            return
        
        # ALTER TABLE 실행 (autocommit 모드)
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE course ADD COLUMN progress INTEGER DEFAULT 0"))
    except Exception as e:
        # 마이그레이션 실패해도 계속 진행 (컬럼이 이미 있을 수 있음)
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Progress column migration: {e}")


def _migrate_add_course_columns() -> None:
    """Course 테이블에 추가 컬럼 추가 (마이그레이션) - persona_profile 포함"""
    try:
        from sqlalchemy import inspect, text
        
        # SQLite인지 확인
        if engine.dialect.name != "sqlite":
            return
        
        # 테이블이 존재하는지 확인
        inspector = inspect(engine)
        if "course" not in inspector.get_table_names():
            return
        
        columns = [col["name"] for col in inspector.get_columns("course")]
        column_info = {col["name"]: col for col in inspector.get_columns("course")}
        
        # category 컬럼 추가
        if "category" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE course ADD COLUMN category TEXT"))
        
        # total_chapters 컬럼 추가
        if "total_chapters" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE course ADD COLUMN total_chapters INTEGER"))
        
        # parent_course_id 컬럼 추가
        if "parent_course_id" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE course ADD COLUMN parent_course_id TEXT"))
        
        # chapter_number 컬럼 추가
        if "chapter_number" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE course ADD COLUMN chapter_number INTEGER"))
        
        # updated_at 컬럼 추가
        if "updated_at" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE course ADD COLUMN updated_at DATETIME"))
        
        # persona_profile 컬럼 추가 (Style Analyzer 결과 저장용)
        if "persona_profile" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE course ADD COLUMN persona_profile TEXT"))
        
        # is_public 컬럼이 NOT NULL로 되어 있으면 기존 데이터에 기본값 설정
        if "is_public" in columns:
            try:
                with engine.begin() as conn:
                    # 기존 NULL 값이 있으면 1(True)로 설정
                    result = conn.execute(text("UPDATE course SET is_public = 1 WHERE is_public IS NULL"))
                    if result.rowcount > 0:
                        print(f"[DB] ✅ is_public 컬럼에 기본값 설정: {result.rowcount}개 행 업데이트")
            except Exception as e:
                # 이미 값이 있거나 오류가 발생해도 계속 진행
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"is_public migration: {e}")
    except Exception as e:
        # 마이그레이션 실패해도 계속 진행 (컬럼이 이미 있을 수 있음)
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Course columns migration: {e}")


def _migrate_add_instructor_profile_columns() -> None:
    """Instructor 테이블에 프로필 관련 컬럼 추가 (마이그레이션)"""
    try:
        from sqlalchemy import inspect, text
        
        # SQLite인지 확인
        if engine.dialect.name != "sqlite":
            return
        
        # 테이블이 존재하는지 확인
        inspector = inspect(engine)
        if "instructor" not in inspector.get_table_names():
            return
        
        columns = [col["name"] for col in inspector.get_columns("instructor")]
        
        # 비밀번호 해시 컬럼 추가
        if "password_hash" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE instructor ADD COLUMN password_hash TEXT"))
        
        # 프로필 이미지 URL 컬럼 추가
        if "profile_image_url" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE instructor ADD COLUMN profile_image_url TEXT"))
        
        # 자기소개 컬럼 추가
        if "bio" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE instructor ADD COLUMN bio TEXT"))
        
        # 전화번호 컬럼 추가
        if "phone" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE instructor ADD COLUMN phone TEXT"))
        
        # 전문 분야 컬럼 추가
        if "specialization" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE instructor ADD COLUMN specialization TEXT"))
        
        # updated_at 컬럼 추가
        if "updated_at" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE instructor ADD COLUMN updated_at DATETIME"))
    except Exception as e:
        # 마이그레이션 실패해도 계속 진행 (컬럼이 이미 있을 수 있음)
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Instructor profile columns migration: {e}")


def init_db() -> None:
    """Create tables if they do not exist."""
    # 데이터베이스 파일 경로 출력
    db_url = settings.database_url
    if db_url.startswith("sqlite"):
        # _prepare_sqlite_url이 이미 처리한 경로를 사용
        # 실제 파일 경로 추출
        from urllib.parse import urlparse
        prepared_url = _prepare_sqlite_url(db_url)
        parsed = urlparse(prepared_url)
        if parsed.path.startswith("///"):
            db_file = Path(parsed.path[3:])
        elif parsed.path.startswith("/"):
            db_file = Path(parsed.path[1:]) if len(parsed.path) > 1 else Path(parsed.path)
        else:
            db_file = Path(parsed.path)
        
        print(f"[DB] 데이터베이스 경로: {db_file}")
        print(f"[DB] 데이터베이스 디렉토리 존재: {db_file.parent.exists()}")
    
    # 테이블 생성
    SQLModel.metadata.create_all(engine)
    print(f"[DB] ✅ 데이터베이스 초기화 완료")
    
    # 데이터베이스 파일 생성 확인
    if db_url.startswith("sqlite"):
        if db_file.exists():
            print(f"[DB] ✅ 데이터베이스 파일 생성됨: {db_file}")
        else:
            print(f"[DB] ⚠️ 데이터베이스 파일이 생성되지 않았습니다: {db_file}")
    
    # 기존 테이블에 progress 컬럼 추가 (마이그레이션)
    _migrate_add_progress_column()
    # Course 테이블에 추가 컬럼 추가 (마이그레이션) - persona_profile 포함
    _migrate_add_course_columns()
    # Instructor 테이블에 프로필 컬럼 추가 (마이그레이션)
    _migrate_add_instructor_profile_columns()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

