#!/usr/bin/env python
"""SQLite 데이터베이스 내용을 확인하는 스크립트"""
import sqlite3
import os
from pathlib import Path
from urllib.parse import urlparse

# 서버 디렉토리 경로
SERVER_DIR = Path(__file__).resolve().parent

# 데이터베이스 경로 확인 (설정 파일과 동일한 로직 사용)
def get_database_path():
    """데이터베이스 파일의 실제 경로를 반환"""
    # 환경 변수에서 DATABASE_URL 확인
    database_url = os.getenv("DATABASE_URL", "sqlite:///./data/yeopgang.db")
    
    if not database_url.startswith("sqlite"):
        return None
    
    # sqlite:/// 경로 파싱
    parsed = urlparse(database_url)
    path = parsed.path
    
    # /// 제거
    if path.startswith("///"):
        file_path = Path(path[3:])
    else:
        file_path = Path(path)
    
    # 상대 경로면 server 디렉토리 기준으로 절대 경로 변환
    if not file_path.is_absolute():
        file_path = SERVER_DIR / file_path
    
    return file_path

# 데이터베이스 경로 가져오기
db_path = get_database_path()

print("=" * 80)
print("📂 데이터베이스 정보")
print("=" * 80)
print(f"경로: {db_path}")
print(f"절대 경로: {db_path.resolve()}")
print(f"파일 존재: {'✅ 예' if db_path.exists() else '❌ 아니오'}")
if db_path.exists():
    file_size = db_path.stat().st_size
    print(f"파일 크기: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    print(f"수정 시간: {db_path.stat().st_mtime}")
print("=" * 80)

if not db_path.exists():
    print(f"\n❌ 데이터베이스 파일이 없습니다: {db_path}")
    print("💡 서버를 한 번 실행하거나 회원가입을 하면 자동으로 생성됩니다.")
    exit(1)

# 데이터베이스 연결
try:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # 컬럼명으로 접근 가능하도록
    cursor = conn.cursor()
except Exception as e:
    print(f"\n❌ 데이터베이스 연결 실패: {e}")
    exit(1)

# 테이블 목록 확인
print("\n📋 테이블 목록:")
print("-" * 80)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
table_names = [table[0] for table in tables]

if tables:
    for i, table in enumerate(tables, 1):
        # 각 테이블의 행 수 확인
        cursor.execute(f'SELECT COUNT(*) FROM "{table[0]}";')
        count = cursor.fetchone()[0]
        print(f"  {i}. {table[0]} ({count}개 행)")
else:
    print("  (테이블이 없습니다)")

# instructor 테이블 상세 정보
if "instructor" in table_names:
    print("\n" + "=" * 80)
    print("👨‍🏫 Instructor 테이블 상세 정보")
    print("=" * 80)
    
    # 컬럼명 확인
    cursor.execute("PRAGMA table_info(instructor);")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print(f"\n컬럼 ({len(column_names)}개): {', '.join(column_names)}")
    
    # 데이터 조회
    cursor.execute("SELECT * FROM instructor ORDER BY created_at DESC;")
    rows = cursor.fetchall()
    
    if rows:
        print(f"\n총 {len(rows)}명의 강사가 등록되어 있습니다:\n")
        for i, row in enumerate(rows, 1):
            print(f"[{i}] 강사 정보")
            print("-" * 80)
            for col_name in column_names:
                value = row[col_name]
                
                # 비밀번호 해시는 일부만 표시
                if col_name == "password_hash" and value:
                    display_value = value[:30] + "..." if len(value) > 30 else value
                # 날짜/시간 형식화
                elif col_name in ["created_at", "updated_at"] and value:
                    display_value = value
                else:
                    display_value = value if value is not None else "(없음)"
                
                # 컬럼명 정렬
                col_display = col_name.ljust(20)
                print(f"  {col_display}: {display_value}")
            print()
    else:
        print("\n등록된 강사가 없습니다.")
        print("💡 회원가입을 하면 여기에 표시됩니다.")

# student 테이블 상세 정보
if "student" in table_names:
    print("\n" + "=" * 80)
    print("👨‍🎓 Student 테이블 상세 정보")
    print("=" * 80)
    
    cursor.execute("SELECT * FROM student ORDER BY created_at DESC;")
    rows = cursor.fetchall()
    
    if rows:
        print(f"\n총 {len(rows)}명의 학생이 등록되어 있습니다:\n")
        for i, row in enumerate(rows, 1):
            print(f"[{i}] {row['id']} - {row['name'] or '(이름 없음)'} ({row['email'] or '(이메일 없음)'})")
    else:
        print("\n등록된 학생이 없습니다.")

# course 테이블 (강의 목록) 상세 정보
if "course" in table_names:
    print("\n" + "=" * 80)
    print("📚 Course 테이블 (강의 목록) 상세 정보")
    print("=" * 80)
    
    # 컬럼 정보
    cursor.execute("PRAGMA table_info(course);")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print(f"\n컬럼 ({len(column_names)}개): {', '.join(column_names)}")
    
    cursor.execute("SELECT COUNT(*) as total, COUNT(DISTINCT instructor_id) as instructors FROM course;")
    stats = cursor.fetchone()
    print(f"\n총 강의 수: {stats[0]}개")
    print(f"강사 수: {stats[1]}명")
    
    if stats[0] > 0:
        print("\n최근 강의:")
        cursor.execute("SELECT id, title, instructor_id, status FROM course ORDER BY created_at DESC LIMIT 5;")
        courses = cursor.fetchall()
        for c in courses:
            print(f"  - {c[0]}: {c[1] or '(제목 없음)'} [{c[3]}]")

# courseenrollment 테이블 요약
if "courseenrollment" in table_names:
    cursor.execute("SELECT COUNT(*) FROM courseenrollment;")
    count = cursor.fetchone()[0]
    print(f"\n📝 CourseEnrollment 테이블: {count}개의 등록 기록")

conn.close()

print("\n" + "=" * 80)
print("✅ 확인 완료!")
print("=" * 80)
print(f"\n💡 데이터베이스 파일 위치: {db_path.resolve()}")
