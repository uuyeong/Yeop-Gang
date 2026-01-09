#!/usr/bin/env python3
"""
테스트용 강사와 강의를 생성하는 스크립트
사용법: python create_test_data.py
"""
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select
from core.db import engine, init_db
from core.models import Instructor, Course, CourseStatus


def create_test_data():
    """테스트용 강사와 강의 생성"""
    # DB 초기화
    init_db()
    
    with Session(engine) as session:
        # 1. 테스트 강사 생성
        test_instructor_id = "test-instructor"
        instructor = session.get(Instructor, test_instructor_id)
        if not instructor:
            instructor = Instructor(
                id=test_instructor_id,
                name="테스트 강사"
            )
            session.add(instructor)
            session.commit()
            print(f"✅ 테스트 강사 생성: {test_instructor_id} (이름: 테스트 강사)")
        else:
            print(f"ℹ️ 테스트 강사 이미 존재: {test_instructor_id}")
        
        # 2. 테스트 강의 생성
        test_course_id = "test-course-1"
        course = session.get(Course, test_course_id)
        if not course:
            course = Course(
                id=test_course_id,
                instructor_id=test_instructor_id,
                title="테스트 강의",
                category="수학",
                status=CourseStatus.completed,
                progress=100
            )
            session.add(course)
            session.commit()
            print(f"✅ 테스트 강의 생성: {test_course_id} (제목: 테스트 강의)")
        else:
            print(f"ℹ️ 테스트 강의 이미 존재: {test_course_id}")
            # 강의 정보 업데이트 (없으면 추가)
            if not course.title:
                course.title = "테스트 강의"
            if not course.category:
                course.category = "수학"
            if course.status != CourseStatus.completed:
                course.status = CourseStatus.completed
                course.progress = 100
            session.commit()
            print(f"✅ 테스트 강의 정보 업데이트: {test_course_id}")
        
        # 3. 추가 테스트 강의 생성 (선택사항)
        test_course_2_id = "test-course-2"
        course2 = session.get(Course, test_course_2_id)
        if not course2:
            course2 = Course(
                id=test_course_2_id,
                instructor_id=test_instructor_id,
                title="테스트 강의 2",
                category="영어",
                status=CourseStatus.completed,
                progress=100
            )
            session.add(course2)
            session.commit()
            print(f"✅ 추가 테스트 강의 생성: {test_course_2_id} (제목: 테스트 강의 2)")
        else:
            print(f"ℹ️ 테스트 강의 2 이미 존재: {test_course_2_id}")
        
        # 4. 생성된 데이터 확인
        print("\n" + "=" * 60)
        print("생성된 데이터 확인")
        print("=" * 60)
        
        instructors = session.exec(select(Instructor)).all()
        print(f"\n강사 수: {len(instructors)}")
        for inst in instructors:
            print(f"  - {inst.id} (이름: {inst.name or '없음'})")
        
        courses = session.exec(select(Course)).all()
        print(f"\n강의 수: {len(courses)}")
        for c in courses:
            print(f"  - {c.id} (제목: {c.title or '없음'}, 강사: {c.instructor_id}, 상태: {c.status.value})")
        
        print("\n" + "=" * 60)
        print("✅ 테스트 데이터 생성 완료!")
        print("=" * 60)
        print(f"\n접속 URL:")
        print(f"  - 강의 시청: http://localhost:3000/student/play/{test_course_id}")
        print(f"  - 강의 목록: http://localhost:3000/student/courses")
        print(f"\n강사 ID: {test_instructor_id}")
        print(f"강의 ID: {test_course_id}")


if __name__ == "__main__":
    try:
        create_test_data()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

