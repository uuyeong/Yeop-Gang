"use client";

/**
 * Design Philosophy: Neo-Brutalism Meets Korean EdTech
 * - Tab-based navigation with bold styling
 * - Course cards with teacher info
 * - Badge explosions for NEW/HOT labels
 */

import { useState, useEffect } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";

const subjects = [
  { id: "all", label: "전체" },
  { id: "korean", label: "국어" },
  { id: "math", label: "수학" },
  { id: "english", label: "영어" },
  { id: "history", label: "한국사" },
  { id: "social", label: "사회" },
  { id: "science", label: "과학" },
  { id: "college", label: "대학별고사" },
];

type Course = {
  id: string;
  title: string;
  category?: string;
  status: string;
  instructor_id: string;
  instructor_name?: string;
  created_at?: string;
  progress: number;
};

export default function CourseSection() {
  const [activeTab, setActiveTab] = useState("all");
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const data = await apiGet<Course[]>("/api/courses");
        // 완료된 강의만 필터링
        const completedCourses = data.filter(c => c.status === "completed");
        setCourses(completedCourses);
      } catch (err) {
        console.error("강의 목록 조회 오류:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCourses();
  }, []);

  // 카테고리별 필터링 (강의명, 카테고리, 강사명 모두 확인)
  const filteredCourses = activeTab === "all" 
    ? courses 
    : courses.filter(course => {
        const subjectMap: { [key: string]: string[] } = {
          korean: ["국어"],
          math: ["수학", "수분감", "수능수학"],
          english: ["영어", "영단어", "영문법"],
          history: ["한국사", "역사"],
          social: ["사회", "사회문화", "생활과윤리"],
          science: ["과학", "물리", "화학", "생물", "생명과학", "지구과학"],
          college: ["대학별고사", "논술", "면접"],
        };
        
        const keywords = subjectMap[activeTab] || [];
        if (keywords.length === 0) return false;
        
        // 강의명, 카테고리, 강사명에서 키워드 검색
        const title = (course.title || "").toLowerCase();
        const category = (course.category || "").toLowerCase();
        const instructorName = (course.instructor_name || "").toLowerCase();
        const courseId = (course.id || "").toLowerCase();
        
        // 하나라도 키워드가 포함되어 있으면 표시
        return keywords.some(keyword => 
          title.includes(keyword.toLowerCase()) ||
          category.includes(keyword.toLowerCase()) ||
          instructorName.includes(keyword.toLowerCase()) ||
          courseId.includes(keyword.toLowerCase())
        );
      });

  // 뱃지 결정 (새로운 강의는 NEW, 인기 강의는 HOT)
  const getBadge = (course: Course, index: number) => {
    if (!course.created_at) return null;
    const daysSinceCreated = Math.floor(
      (Date.now() - new Date(course.created_at).getTime()) / (1000 * 60 * 60 * 24)
    );
    if (daysSinceCreated < 7) return "NEW";
    // 인덱스 기반으로 일관된 뱃지 결정 (랜덤 대신)
    if (index % 3 === 0) return "HOT";
    return null;
  };

  return (
    <div className="bg-white py-12">
      <div className="container">
        <h2
          className="text-4xl mb-8 text-center"
          style={{ fontFamily: "var(--font-display)" }}
        >
          열공하는 수험생을 위한 HOT PICK
        </h2>

        {/* Subject Tabs */}
        <div className="flex justify-center gap-2 mb-8 flex-wrap">
          {subjects.map((subject) => (
            <button
              key={subject.id}
              onClick={() => setActiveTab(subject.id)}
              className={`px-6 py-3 border border-gray-400 rounded-lg font-bold transition-all duration-150 ${
                activeTab === subject.id
                  ? "bg-primary text-white scale-105"
                  : "bg-white hover:bg-gray-50 hover:scale-105"
              }`}
            >
              {subject.label}
            </button>
          ))}
        </div>

        {/* Course Cards */}
        {isLoading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">강의를 불러오는 중...</p>
          </div>
        ) : filteredCourses.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">등록된 강의가 없습니다.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCourses.map((course, index) => {
              const badge = getBadge(course, index);
              return (
                <Link
                  key={course.id}
                  href={`/student/courses/${course.instructor_id}/${course.id}/chapters`}
                  className="bg-white border-2 border-gray-400 rounded-lg p-6 hover:scale-105 transition-all duration-150 cursor-pointer relative overflow-hidden block"
                >
                  {/* Badge */}
                  {badge && (
                    <div className="absolute top-4 right-4 z-10">
                      <span
                        className={`border border-gray-400 font-bold px-3 py-1 rounded-lg text-sm ${
                          badge === "HOT"
                            ? "bg-accent text-white"
                            : "bg-secondary text-white"
                        }`}
                      >
                        {badge}
                      </span>
                    </div>
                  )}

                  {/* Course Image Placeholder */}
                  <div className="bg-primary h-48 rounded-lg mb-4 border border-gray-400 flex items-center justify-center text-white text-6xl font-bold">
                    {course.instructor_name?.[0] || course.instructor_id[0] || "강"}
                  </div>

                  {/* Course Info */}
                  <div className="space-y-2">
                    <p className="text-sm text-gray-600 font-medium">
                      {course.instructor_name || course.instructor_id}
                    </p>
                    <h3 className="text-xl font-bold line-clamp-2">{course.title || course.id}</h3>
                    {course.category && (
                      <p className="text-xs text-gray-500">{course.category}</p>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

