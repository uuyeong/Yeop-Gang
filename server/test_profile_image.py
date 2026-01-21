#!/usr/bin/env python
"""프로필 이미지 저장/로드 테스트 스크립트"""
import sqlite3
import os
from pathlib import Path
from urllib.parse import urlparse

# 서버 디렉토리 경로
SERVER_DIR = Path(__file__).resolve().parent

def get_database_path():
    """데이터베이스 파일의 실제 경로를 반환"""
    database_url = os.getenv("DATABASE_URL", "sqlite:///./data/yeopgang.db")
    
    if not database_url.startswith("sqlite"):
        return None
    
    parsed = urlparse(database_url)
    path = parsed.path
    
    if path.startswith("///"):
        file_path = Path(path[3:])
    else:
        file_path = Path(path)
    
    if not file_path.is_absolute():
        file_path = SERVER_DIR / file_path
    
    return file_path.resolve()

def test_profile_image():
    """프로필 이미지 저장 상태 확인"""
    db_path = get_database_path()
    if not db_path or not db_path.exists():
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
    
    print(f"📁 데이터베이스 경로: {db_path}")
    print("-" * 80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Instructor 테이블의 프로필 이미지 정보 확인
    cursor.execute("""
        SELECT 
            id, 
            name, 
            email,
            CASE 
                WHEN profile_image_url IS NULL THEN 'NULL'
                WHEN profile_image_url = '' THEN '빈 문자열'
                ELSE '값 있음'
            END as image_status,
            CASE 
                WHEN profile_image_url IS NULL THEN 0
                ELSE LENGTH(profile_image_url)
            END as image_length,
            CASE 
                WHEN profile_image_url IS NULL THEN NULL
                ELSE SUBSTR(profile_image_url, 1, 50)
            END as image_preview
        FROM instructor
        ORDER BY id
    """)
    
    instructors = cursor.fetchall()
    
    if not instructors:
        print("❌ Instructor 레코드가 없습니다.")
        conn.close()
        return
    
    print(f"✅ 총 {len(instructors)}명의 강사가 있습니다.\n")
    
    for row in instructors:
        instructor_id, name, email, image_status, image_length, image_preview = row
        print(f"강사 ID: {instructor_id}")
        print(f"  이름: {name}")
        print(f"  이메일: {email}")
        print(f"  프로필 이미지 상태: {image_status}")
        if image_length > 0:
            print(f"  이미지 URL 길이: {image_length} 문자")
            print(f"  이미지 URL 미리보기: {image_preview}...")
            if image_preview and image_preview.startswith("data:image"):
                print(f"  ✅ Base64 데이터 URL 형식입니다.")
            else:
                print(f"  ⚠️  Base64 데이터 URL 형식이 아닙니다.")
        print()
    
    conn.close()
    print("-" * 80)
    print("테스트 완료!")

if __name__ == "__main__":
    test_profile_image()
