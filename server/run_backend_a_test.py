#!/usr/bin/env python3
"""
Backend A 테스트 스크립트
ref/testcourse1, testcourse2 파일들로 챗봇 생성
"""
import sys
import json
import shutil
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ai.pipelines.processor import process_course_assets
from core.config import AppSettings
from core.db import init_db, engine
from core.models import Course, CourseStatus, Instructor, Video
from sqlmodel import Session, select


def find_files_in_directory(course_dir: Path):
    """업로드 디렉토리에서 파일 찾기"""
    files = {
        "video": None,
        "audio": None,
        "pdf": None,
        "smi": None,
    }
    
    # 비디오 파일 찾기
    video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    for ext in video_extensions:
        for video_file in course_dir.glob(f"*{ext}"):
            files["video"] = video_file
            print(f"✅ 비디오 파일 발견: {video_file.name}")
            break
        if files["video"]:
            break
    
    # 오디오 파일 찾기
    audio_extensions = [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"]
    for ext in audio_extensions:
        for audio_file in course_dir.glob(f"*{ext}"):
            files["audio"] = audio_file
            print(f"✅ 오디오 파일 발견: {audio_file.name}")
            break
        if files["audio"]:
            break
    
    # PDF 파일 찾기
    for pdf_file in course_dir.glob("*.pdf"):
        files["pdf"] = pdf_file
        print(f"✅ PDF 파일 발견: {pdf_file.name}")
        break
    
    # SMI 자막 파일 찾기 (여러 개 있으면 첫 번째 것 사용)
    smi_files = list(course_dir.glob("*.smi"))
    if smi_files:
        files["smi"] = smi_files[0]  # 첫 번째 SMI 파일 사용
        print(f"✅ SMI 자막 파일 발견: {smi_files[0].name}")
        if len(smi_files) > 1:
            print(f"   ⚠️ SMI 파일이 {len(smi_files)}개 있습니다. 첫 번째 파일을 사용합니다.")
            for smi in smi_files[1:]:
                print(f"      - {smi.name} (사용 안 함)")
    
    return files


def update_progress_callback(progress: int, message: str):
    """진행률 업데이트 콜백"""
    print(f"[진행률 {progress}%] {message}")


def test_course(
    course_number: int,
    instructor_id: str,
    course_id: str,
    ref_dir: Path
):
    """단일 강의 테스트"""
    print("\n" + "=" * 80)
    print(f"테스트 강의 {course_number}: {course_id}")
    print("=" * 80)
    
    print(f"\n📁 Ref 디렉토리: {ref_dir}")
    
    if not ref_dir.exists():
        print(f"❌ Ref 디렉토리가 존재하지 않습니다: {ref_dir}")
        return False
    
    # 파일 찾기
    print(f"\n📂 파일 검색 중...")
    files = find_files_in_directory(ref_dir)
    
    # 찾은 파일 요약
    print(f"\n📋 찾은 파일:")
    found_any = False
    for file_type, file_path in files.items():
        if file_path:
            print(f"  - {file_type}: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)")
            found_any = True
        else:
            print(f"  - {file_type}: 없음")
    
    # 최소한 하나의 파일은 있어야 함
    if not found_any:
        print(f"\n❌ 처리할 파일이 없습니다!")
        return False
    
    # 파일을 data/uploads로 복사
    settings = AppSettings()
    upload_dir = settings.uploads_dir / instructor_id / course_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    copied_files = {}
    print(f"\n📋 파일을 data/uploads로 복사 중...")
    print(f"   대상 디렉토리: {upload_dir}")
    
    for file_type, file_path in files.items():
        if file_path and file_path.exists():
            # 파일 복사
            dest_path = upload_dir / file_path.name
            if not dest_path.exists() or dest_path.stat().st_size != file_path.stat().st_size:
                shutil.copy2(file_path, dest_path)
                print(f"  ✅ {file_type}: {file_path.name} -> {dest_path}")
            else:
                print(f"  ⏭️  {file_type}: {file_path.name} (이미 존재)")
            copied_files[file_type] = dest_path
    
    # 복사된 파일 경로로 파이프라인 실행
    print(f"\n🚀 Backend A 파이프라인 시작...")
    print(f"   강사 ID: {instructor_id}")
    print(f"   강의 ID: {course_id}")
    print()
    
    try:
        result = process_course_assets(
            course_id=course_id,
            instructor_id=instructor_id,
            video_path=copied_files.get("video"),
            audio_path=copied_files.get("audio"),
            pdf_path=copied_files.get("pdf"),
            smi_path=copied_files.get("smi"),
            update_progress=update_progress_callback,
        )
        
        print("\n" + "=" * 80)
        if result.get("status") == "completed":
            print(f"✅ Backend A 파이프라인 완료! (강의 {course_number})")
            print("=" * 80)
            print(f"\n📊 처리 결과:")
            print(f"  - 인제스트된 문서 수: {result.get('ingested_count', 0)}")
            if result.get("transcript_path"):
                print(f"  - Transcript 파일: {result.get('transcript_path')}")
            if result.get("persona_profile"):
                print(f"  - Persona Profile: {result.get('persona_profile')[:100]}...")
            
            # DB에 Instructor 및 Course 생성 (테스트용)
            with Session(engine) as session:
                # Instructor 생성/확인
                instructor = session.get(Instructor, instructor_id)
                if not instructor:
                    instructor = Instructor(
                        id=instructor_id,
                        name=f"테스트 강사 {course_number}",
                        email=f"test-instructor-{course_number}@example.com"
                    )
                    session.add(instructor)
                    session.commit()
                    print(f"✅ Instructor 생성: {instructor_id}")
                
                # Course 생성/업데이트
                course = session.get(Course, course_id)
                if not course:
                    course = Course(
                        id=course_id,
                        instructor_id=instructor_id,
                        title=f"테스트 강의 {course_number}",
                        status=CourseStatus.completed,
                        progress=100,
                    )
                    session.add(course)
                    print(f"✅ Course 생성: {course_id}")
                else:
                    course.status = CourseStatus.completed
                    course.progress = 100
                    print(f"✅ Course 업데이트: {course_id}")
                
                # persona_profile 저장
                if result.get("persona_profile"):
                    course.persona_profile = result.get("persona_profile")
                    print(f"✅ Persona Profile 저장: {course_id}")
                
                # Video 레코드 생성 (비디오/오디오/PDF 파일)
                for file_type in ["video", "audio", "pdf"]:
                    if copied_files.get(file_type):
                        file_path = copied_files[file_type]
                        # 기존 레코드 확인
                        existing = session.exec(
                            select(Video).where(
                                Video.course_id == course_id,
                                Video.filename == file_path.name
                            )
                        ).first()
                        
                        if not existing:
                            video_record = Video(
                                course_id=course_id,
                                filename=file_path.name,
                                storage_path=str(file_path.resolve()),
                                filetype=file_type,
                                transcript_path=result.get("transcript_path") if file_type in ["audio", "video"] else None
                            )
                            session.add(video_record)
                            print(f"✅ Video 레코드 생성: {file_path.name} ({file_type})")
                        else:
                            # 기존 레코드 업데이트
                            existing.storage_path = str(file_path.resolve())
                            if file_type in ["audio", "video"] and result.get("transcript_path"):
                                existing.transcript_path = result.get("transcript_path")
                            print(f"✅ Video 레코드 업데이트: {file_path.name} ({file_type})")
                
                session.commit()
            
            print(f"\n🎉 챗봇 생성 완료! (강의 {course_number})")
            print(f"\n📝 테스트 방법:")
            print(f"  1. 프론트엔드 접속: http://localhost:3000/student/play/{course_id}")
            print(f"  2. 챗봇에 질문하기")
            print(f"  3. 시간 관련 질문: '지금 몇분대야?', '방금 뭐라고 했어?'")
            return True
        else:
            print(f"❌ Backend A 파이프라인 실패 (강의 {course_number})")
            print("=" * 80)
            error = result.get("error", "알 수 없는 오류")
            print(f"\n❌ 오류: {error}")
            print(f"\n💡 확인 사항:")
            print(f"  - OPENAI_API_KEY가 설정되어 있는지")
            print(f"  - 파일 형식이 올바른지")
            print(f"  - 파일 크기가 적절한지")
            return False
            
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ 오류 발생 (강의 {course_number})")
        print("=" * 80)
        print(f"\n❌ 오류 메시지: {e}")
        import traceback
        print(f"\n상세 오류:")
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    print("=" * 80)
    print("Backend A 테스트: 챗봇 생성 (testcourse1, testcourse2)")
    print("=" * 80)
    
    # 프로젝트 루트 확인
    project_root = Path(__file__).resolve().parent.parent
    ref_dir = project_root / "ref"
    
    print(f"\n📁 프로젝트 루트: {project_root}")
    print(f"📁 Ref 디렉토리: {ref_dir}")
    
    if not ref_dir.exists():
        print(f"❌ Ref 디렉토리가 존재하지 않습니다: {ref_dir}")
        return
    
    # DB 초기화
    print("\n🔧 데이터베이스 초기화 중...")
    init_db()
    print("✅ 데이터베이스 초기화 완료")
    
    # 테스트 강의 설정
    test_courses = [
        {
            "number": 1,
            "instructor_id": "test-instructor-1",
            "course_id": "test-course-1",
            "ref_dir": ref_dir / "testcourse1"
        },
        {
            "number": 2,
            "instructor_id": "test-instructor-2",
            "course_id": "test-course-2",
            "ref_dir": ref_dir / "testcourse2"
        }
    ]
    
    # 각 강의 테스트
    results = []
    for test_course_config in test_courses:
        success = test_course(
            course_number=test_course_config["number"],
            instructor_id=test_course_config["instructor_id"],
            course_id=test_course_config["course_id"],
            ref_dir=test_course_config["ref_dir"]
        )
        results.append(success)
    
    # 최종 결과 요약
    print("\n" + "=" * 80)
    print("최종 결과 요약")
    print("=" * 80)
    for i, success in enumerate(results, 1):
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  테스트 강의 {i}: {status}")
    
    total_success = sum(results)
    total_tests = len(results)
    print(f"\n전체: {total_success}/{total_tests} 성공")
    
    if total_success == total_tests:
        print("\n🎉 모든 테스트가 성공했습니다!")
    else:
        print(f"\n⚠️ {total_tests - total_success}개 테스트가 실패했습니다.")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
