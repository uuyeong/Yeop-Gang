import logging
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from core.config import AppSettings

logger = logging.getLogger(__name__)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_upload_file(file: UploadFile, base_dir: Path) -> Path:
    try:
        logger.info(f"💾 파일 저장 시작 - filename: {file.filename}, base_dir: {base_dir}")
        ensure_dir(base_dir)
        target = base_dir / file.filename
        logger.info(f"💾 파일 저장 경로: {target}")
        
        # 파일 읽기
        file_content = file.file.read()
        file_size = len(file_content)
        logger.info(f"💾 파일 크기: {file_size} bytes")
        
        # 파일 쓰기
        with target.open("wb") as f:
            f.write(file_content)
        
        # 파일 포인터를 처음으로 되돌림 (다른 곳에서 사용할 수 있도록)
        file.file.seek(0)
        
        logger.info(f"✅ 파일 저장 완료 - {target} ({file_size} bytes)")
        return target
    except Exception as e:
        logger.error(f"❌ 파일 저장 실패 - filename: {file.filename}, error: {e}", exc_info=True)
        raise


def save_course_assets(
    instructor_id: str,
    course_id: str,
    video: Optional[UploadFile] = None,
    audio: Optional[UploadFile] = None,
    pdf: Optional[UploadFile] = None,
    smi: Optional[UploadFile] = None,
    settings: Optional[AppSettings] = None,
) -> dict[str, Optional[Path]]:
    try:
        logger.info(f"💾 강의 파일 저장 시작 - instructor_id: {instructor_id}, course_id: {course_id}")
        logger.info(f"💾 파일 정보 - video: {video.filename if video else None}, audio: {audio.filename if audio else None}, pdf: {pdf.filename if pdf else None}, smi: {smi.filename if smi else None}")
        
        settings = settings or AppSettings()
        course_dir = settings.uploads_dir / instructor_id / course_id
        logger.info(f"💾 강의 디렉토리: {course_dir}")
        ensure_dir(course_dir)
        logger.info(f"✅ 강의 디렉토리 생성 완료: {course_dir}")

        paths: dict[str, Optional[Path]] = {"video": None, "audio": None, "pdf": None, "smi": None}
        
        if video:
            logger.info(f"💾 비디오 파일 저장 중...")
            paths["video"] = save_upload_file(video, course_dir)
        if audio:
            logger.info(f"💾 오디오 파일 저장 중...")
            paths["audio"] = save_upload_file(audio, course_dir)
        if pdf:
            logger.info(f"💾 PDF 파일 저장 중...")
            paths["pdf"] = save_upload_file(pdf, course_dir)
        if smi:
            logger.info(f"💾 SMI 파일 저장 중...")
            paths["smi"] = save_upload_file(smi, course_dir)
        
        logger.info(f"✅ 강의 파일 저장 완료 - paths: {paths}")
        return paths
    except Exception as e:
        logger.error(f"❌ 강의 파일 저장 실패 - instructor_id: {instructor_id}, course_id: {course_id}, error: {e}", exc_info=True)
        raise

