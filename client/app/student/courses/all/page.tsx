"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, BookOpen, User, Loader2, AlertCircle } from "lucide-react";
import { apiGet, handleApiError } from "@/lib/api";

const categories = [
  { id: "all", label: "전체" },
  { id: "국어", label: "국어" },
  { id: "수학", label: "수학" },
  { id: "영어", label: "영어" },
  { id: "한국사", label: "한국사" },
  { id: "물리", label: "물리" },
  { id: "화학", label: "화학" },
  { id: "생명과학", label: "생명과학" },
  { id: "지구과학", label: "지구과학" },
  { id: "사회", label: "사회" },
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

export default function AllCoursesPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("all");
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCourses();
  }, [activeTab]);

  const fetchCourses = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // 모든 강의 가져오기
      const data = await apiGet<Course[]>(`/api/courses`);
      // 완료된 강의만 필터링
      let completedCourses = data.filter(c => c.status === "completed");
      
      // 카테고리별 필터링
      if (activeTab !== "all") {
        const categoryMap: { [key: string]: string[] } = {
          "국어": ["국어"],
          "수학": ["수학", "수분감", "수능수학"],
          "영어": ["영어", "영단어", "영문법"],
          "한국사": ["한국사"],
          "사회": ["사회", "사회문화", "생활과윤리"],
          "물리": ["물리"],
          "화학": ["화학"],
          "생명과학": ["생명과학", "생물"],
          "지구과학": ["지구과학"],
        };
        
        const keywords = categoryMap[activeTab] || [];
        if (keywords.length > 0) {
          completedCourses = completedCourses.filter(course => {
            const title = (course.title || "").toLowerCase();
            const category = (course.category || "").toLowerCase();
            const courseId = (course.id || "").toLowerCase();
            
            // 제목, 카테고리, 강의 ID에서 키워드 검색
            return keywords.some(keyword => 
              title.includes(keyword.toLowerCase()) ||
              category.includes(keyword.toLowerCase()) ||
              courseId.includes(keyword.toLowerCase())
            );
          });
        }
      }
      
      setCourses(completedCourses);
    } catch (err) {
      console.error("강의 목록 조회 오류:", err);
      const apiError = handleApiError(err);
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
            수강 가능
          </span>
        );
      case "processing":
        return (
          <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800">
            제작 중
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
            {status}
          </span>
        );
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 sm:px-6 py-6 sm:py-10">
        {/* 네비게이션 */}
        <div className="mb-4 sm:mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs sm:text-sm text-slate-600 transition-colors hover:text-slate-900"
          >
            <ArrowLeft className="h-3 w-3 sm:h-4 sm:w-4" />
            <span>홈으로</span>
          </Link>
        </div>

        {/* 헤더 */}
        <header className="mb-6 sm:mb-8">
          <div className="mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
            <div className="flex h-8 w-8 sm:h-10 sm:w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600 flex-shrink-0">
              <BookOpen className="h-4 w-4 sm:h-5 sm:w-5" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-slate-900">모든 강좌</h1>
              <p className="mt-0.5 sm:mt-1 text-xs sm:text-sm text-slate-500">
                과목별로 강의를 선택하세요
              </p>
            </div>
          </div>

          {/* 카테고리 탭 */}
          <div className="flex flex-wrap gap-2 sm:gap-3">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setActiveTab(category.id)}
                className={`px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 rounded-lg border text-xs sm:text-sm transition-all duration-150 ${
                  activeTab === category.id
                    ? "bg-primary text-white border-primary"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                }`}
              >
                {category.label}
              </button>
            ))}
          </div>
        </header>

        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-3 sm:gap-4 py-8 sm:py-16">
            <Loader2 className="h-6 w-6 sm:h-8 sm:w-8 animate-spin text-blue-600" />
            <span className="text-xs sm:text-sm text-slate-600">강의 목록을 불러오는 중...</span>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 sm:p-6">
            <div className="mb-3 sm:mb-4 flex items-start gap-2 sm:gap-3">
              <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 flex-shrink-0 text-red-600" />
              <div className="flex-1">
                <h3 className="mb-1 text-xs sm:text-sm font-semibold text-red-900">오류 발생</h3>
                <p className="text-xs sm:text-sm text-red-700">{error}</p>
              </div>
            </div>
            <button
              onClick={fetchCourses}
              className="w-full rounded-lg bg-red-600 px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium text-white transition-colors hover:bg-red-700"
            >
              다시 시도
            </button>
          </div>
        )}

        {!isLoading && !error && (
          <>
            {courses.length === 0 ? (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-12 text-center shadow-sm">
                <div className="mb-3 sm:mb-4 inline-flex h-12 w-12 sm:h-16 sm:w-16 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                  <BookOpen className="h-6 w-6 sm:h-8 sm:w-8" />
                </div>
                <h3 className="mb-1 sm:mb-2 text-base sm:text-lg font-semibold text-slate-900">
                  {activeTab === "all" ? "등록된 강의가 없습니다" : `${categories.find(c => c.id === activeTab)?.label} 강의가 없습니다`}
                </h3>
                <p className="text-xs sm:text-sm text-slate-600">
                  강의가 업로드되면 목록이 표시됩니다
                </p>
              </div>
            ) : (
              <div className="grid gap-4 sm:gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                {courses.map((course) => (
                  <Link
                    key={course.id}
                    href={`/student/courses/${course.instructor_id}/${course.id}/chapters`}
                    className="group rounded-2xl border border-slate-200 bg-white p-4 sm:p-6 shadow-sm transition-all hover:border-blue-300 hover:shadow-lg"
                  >
                    <div className="mb-3 sm:mb-4">
                      <div className="mb-2 sm:mb-3 flex items-start justify-between">
                        <h3 className="flex-1 text-base sm:text-lg font-semibold text-slate-900 transition-colors group-hover:text-blue-600 line-clamp-2">
                          {course.title}
                        </h3>
                      </div>
                      {course.instructor_name && (
                        <div className="mb-2 sm:mb-3 flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm text-slate-600">
                          <User className="h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" />
                          <span className="truncate">{course.instructor_name}</span>
                        </div>
                      )}
                      {course.category && (
                        <div className="mb-2 sm:mb-3">
                          <span className="inline-flex items-center rounded-full bg-blue-100 px-2 sm:px-2.5 py-0.5 text-xs font-medium text-blue-800">
                            {course.category}
                          </span>
                        </div>
                      )}
                      <div className="mb-2 sm:mb-3">
                        {getStatusBadge(course.status)}
                      </div>
                    </div>
                    <div className="flex items-center justify-between rounded-lg bg-blue-50 px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm font-medium text-blue-700 transition-colors group-hover:bg-blue-100">
                      <span>강의 보기</span>
                      <BookOpen className="h-3 w-3 sm:h-4 sm:w-4" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}

