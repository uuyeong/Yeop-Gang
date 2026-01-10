#!/usr/bin/env python3
"""
Backend A 테스트 스크립트
data/uploads에 있는 파일들로 챗봇 생성
"""
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ai.pipelines.processor import process_course_assets
from core.config import AppSettings


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


def main():
    """메인 함수"""
    print("=" * 60)
    print("Backend A 테스트: 챗봇 생성")
    print("=" * 60)
    
    # 설정
    instructor_id = "test-instructor-1"
    course_id = "test-course-1"
    
    # 업로드 디렉토리 확인
    settings = AppSettings()
    course_dir = settings.uploads_dir / instructor_id / course_id
    
    print(f"\n📁 업로드 디렉토리: {course_dir}")
    
    if not course_dir.exists():
        print(f"❌ 디렉토리가 존재하지 않습니다: {course_dir}")
        print(f"💡 다음 경로에 파일을 넣어주세요:")
        print(f"   {course_dir}")
        return
    
    print(f"✅ 디렉토리 존재 확인")
    
    # 파일 찾기
    print(f"\n📂 파일 검색 중...")
    files = find_files_in_directory(course_dir)
    
    # 찾은 파일 요약
    print(f"\n📋 찾은 파일:")
    for file_type, file_path in files.items():
        if file_path:
            print(f"  - {file_type}: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)")
        else:
            print(f"  - {file_type}: 없음")
    
    # 최소한 하나의 파일은 있어야 함
    if not any(files.values()):
        print(f"\n❌ 처리할 파일이 없습니다!")
        print(f"💡 다음 중 하나 이상의 파일이 필요합니다:")
        print(f"   - 비디오/오디오 파일 (.mp4, .mp3 등)")
        print(f"   - PDF 파일 (.pdf)")
        print(f"   - SMI 자막 파일 (.smi)")
        return
    
    # Backend A 파이프라인 실행
    print(f"\n🚀 Backend A 파이프라인 시작...")
    print(f"   강사 ID: {instructor_id}")
    print(f"   강의 ID: {course_id}")
    print()
    
    try:
        result = process_course_assets(
            course_id=course_id,
            instructor_id=instructor_id,
            video_path=files["video"],
            audio_path=files["audio"],
            pdf_path=files["pdf"],
            smi_path=files["smi"],
            update_progress=update_progress_callback,
        )
        
        print("\n" + "=" * 60)
        if result.get("status") == "completed":
            print("✅ Backend A 파이프라인 완료!")
            print("=" * 60)
            print(f"\n📊 처리 결과:")
            print(f"  - 인제스트된 문서 수: {result.get('ingested_count', 0)}")
            if result.get("transcript_path"):
                print(f"  - Transcript 파일: {result.get('transcript_path')}")
            
            print(f"\n🎉 챗봇 생성 완료!")
            print(f"\n📝 테스트 방법:")
            print(f"  1. 프론트엔드 접속: http://localhost:3000/student/play/{course_id}")
            print(f"  2. 챗봇에 질문하기")
            print(f"  3. 시간 관련 질문: '지금 몇분대야?', '방금 뭐라고 했어?'")
        else:
            print("❌ Backend A 파이프라인 실패")
            print("=" * 60)
            error = result.get("error", "알 수 없는 오류")
            print(f"\n❌ 오류: {error}")
            print(f"\n💡 확인 사항:")
            print(f"  - OPENAI_API_KEY가 설정되어 있는지")
            print(f"  - 파일 형식이 올바른지")
            print(f"  - 파일 크기가 적절한지")
            
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 오류 발생")
        print("=" * 60)
        print(f"\n❌ 오류 메시지: {e}")
        import traceback
        print(f"\n상세 오류:")
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

