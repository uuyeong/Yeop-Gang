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
];

type Course = {
  id: string;
  title: string;
  category?: string;
  status: string;
  instructor_id: string;
  instructor_name?: string;
  instructor_profile_image_url?: string;
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
        // 최신 강의순으로 정렬 (created_at 기준)
        const sortedCourses = completedCourses.sort((a, b) => {
          const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
          const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
          return dateB - dateA; // 최신순 (내림차순)
        });
        setCourses(sortedCourses);
      } catch (err) {
        console.error("강의 목록 조회 오류:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCourses();
  }, []);

  // 과목별 필터링 (강의명, 과목, 강사명 모두 확인)
  const filteredCourses = activeTab === "all" 
    ? courses 
    : courses.filter(course => {
        const subjectMap: { [key: string]: string[] } = {
          korean: ["국어"],
          math: ["수학", "수분감", "수능수학"],
          english: ["영어", "영단어", "영문법"],
          history: ["한국사"],
          social: ["사회", "사회문화", "생활과윤리"],
          science: ["과학", "물리", "화학", "생물", "생명과학", "지구과학"],
        };
        
        const keywords = subjectMap[activeTab] || [];
        if (keywords.length === 0) return false;
        
        // 강의명, 과목, 강사명에서 키워드 검색
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
    <div className="bg-white py-8 sm:py-12 md:py-16 pb-16 sm:pb-24 md:pb-32">
      <div className="container">
        <h2
          className="text-2xl sm:text-3xl md:text-4xl mb-6 sm:mb-8 md:mb-12 text-center px-4"
          style={{ fontFamily: "var(--font-display)" }}
        >
          이달의 강좌
        </h2>

        {/* Subject Tabs */}
        <div className="flex justify-center gap-2 sm:gap-3 mb-6 sm:mb-8 md:mb-12 flex-wrap px-4">
          {subjects.map((subject) => (
            <button
              key={subject.id}
              onClick={() => setActiveTab(subject.id)}
              className={`px-3 sm:px-4 md:px-6 py-2 sm:py-2.5 md:py-3 rounded-lg font-bold text-xs sm:text-sm md:text-base transition-all duration-150 ${
                activeTab === subject.id
                  ? "bg-primary text-white scale-105 border border-transparent"
                  : "bg-white border border-gray-400 hover:bg-gray-50 hover:scale-105"
              }`}
            >
              {subject.label}
            </button>
          ))}
        </div>

        {/* Course Cards */}
        {isLoading ? (
          <div className="text-center py-8 sm:py-12">
            <p className="text-gray-500 text-sm sm:text-base">강의를 불러오는 중...</p>
          </div>
        ) : filteredCourses.length === 0 ? (
          <div className="text-center py-8 sm:py-12">
            <p className="text-gray-500 text-sm sm:text-base">등록된 강의가 없습니다.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 md:gap-8 px-4 sm:px-0">
            {filteredCourses.slice(0, 6).map((course, index) => {
              const badge = getBadge(course, index);
              return (
                <Link
                  key={course.id}
                  href={`/student/courses/${course.instructor_id}/${course.id}/chapters`}
                  className="bg-white border border-gray-400 rounded-lg p-4 sm:p-6 md:p-8 hover:scale-105 transition-all duration-150 cursor-pointer relative overflow-hidden block"
                >
                  {/* Badge */}
                  {badge && (
                    <div className="absolute top-2 sm:top-4 right-2 sm:right-4 z-10">
                      <span
                        className={`font-bold px-2 sm:px-3 py-0.5 sm:py-1 rounded-lg text-xs sm:text-sm ${
                          badge === "HOT"
                            ? "bg-accent text-white border border-gray-400"
                            : "bg-secondary text-white border border-transparent"
                        }`}
                      >
                        {badge}
                      </span>
                    </div>
                  )}

                  {/* Instructor Profile Image */}
                  <div className="h-32 sm:h-40 md:h-48 rounded-lg mb-3 sm:mb-4 border border-gray-400 overflow-hidden flex items-center justify-center bg-gray-100">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={course.instructor_profile_image_url || "https://i.ibb.co/27yY0pLS/default-profile.png"}
                      alt={course.instructor_name || course.instructor_id}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  {/* Course Info */}
                  <div className="space-y-1 sm:space-y-2">
                    <p className="text-xs sm:text-sm text-gray-600 font-medium">
                      {course.instructor_name ? `${course.instructor_name} 선생님` : `${course.instructor_id} 선생님`}
                    </p>
                    <h3 className="text-base sm:text-lg md:text-xl font-bold line-clamp-2">{course.title || course.id}</h3>
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

