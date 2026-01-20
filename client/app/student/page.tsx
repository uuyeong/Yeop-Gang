"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Trash2, AlertCircle, ArrowLeft, BookOpen, Clock, User, PlayCircle, CheckCircle2, Loader2, XCircle, Search, Filter, X } from "lucide-react";
import { apiGet, apiDelete, handleApiError } from "../../lib/api";
import { getUser } from "../../lib/auth";

type Course = {
  id: string;
  title: string;
  category?: string;
  status: string;
  instructor_id: string;
  instructor_name?: string;
  instructor_specialization?: string;
  created_at?: string;
  progress: number;
};

export default function StudentPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingCourseId, setDeletingCourseId] = useState<string | null>(null);
  const [isInstructor, setIsInstructor] = useState(false);
  
  // 검색 및 필터 상태
  const [searchQuery, setSearchQuery] = useState("");
  const [specializationFilter, setSpecializationFilter] = useState<string>("all"); // 과목 종류 (수학, 생명과학 등)
  const [categoryFilter, setCategoryFilter] = useState<string>("all"); // 카테고리 (개념강의 등)

  useEffect(() => {
    // 강사 로그인 여부 확인
    const user = getUser();
    setIsInstructor(user?.role === "instructor");
    
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiGet<Course[]>("/api/courses");
      setCourses(data);
    } catch (err) {
      console.error("강의 목록 조회 오류:", err);
      // 오류는 콘솔에만 기록하고 화면에는 표시하지 않음
      // const apiError = handleApiError(err);
      // setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (courseId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!confirm(`강의 '${courseId}'를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) {
      return;
    }
    
    setDeletingCourseId(courseId);
    
    try {
      await apiDelete(`/api/courses/${courseId}`);
      
      // 목록에서 제거
      setCourses((prev) => prev.filter((c) => c.id !== courseId));
    } catch (err) {
      console.error("강의 삭제 오류:", err);
      const apiError = handleApiError(err);
      alert(`강의 삭제 실패: ${apiError.message}`);
    } finally {
      setDeletingCourseId(null);
    }
  };

  // 필터링된 강의 목록
  const filteredCourses = courses.filter((course) => {
    // 검색어 필터 (강의 제목 또는 선생님 이름)
    const matchesSearch =
      searchQuery === "" ||
      course.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.instructor_name?.toLowerCase().includes(searchQuery.toLowerCase());
    
    // 과목 종류 필터 (선생님의 세부분야 - 수학, 생명과학 등)
    const matchesSpecialization = specializationFilter === "all" || course.instructor_specialization === specializationFilter;
    
    // 카테고리 필터 (개념강의 등)
    const matchesCategory = categoryFilter === "all" || course.category === categoryFilter;
    
    return matchesSearch && matchesSpecialization && matchesCategory;
  });

  // 사용 가능한 과목 종류 목록 (선생님의 세부분야)
  const specializations = Array.from(new Set(courses.map((c) => c.instructor_specialization).filter(Boolean))) as string[];
  
  // 사용 가능한 카테고리 목록
  const categories = Array.from(new Set(courses.map((c) => c.category).filter(Boolean))) as string[];

  // 필터 초기화
  const resetFilters = () => {
    setSearchQuery("");
    setSpecializationFilter("all");
    setCategoryFilter("all");
  };

  const hasActiveFilters = searchQuery !== "" || specializationFilter !== "all" || categoryFilter !== "all";

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>완료</span>
          </span>
        );
      case "processing":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-3 py-1 text-xs font-medium text-yellow-700">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>처리 중</span>
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700">
            <XCircle className="h-3.5 w-3.5" />
            <span>실패</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
            <span>{status}</span>
          </span>
        );
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="mx-auto max-w-6xl px-6 py-10">
        {/* 네비게이션 */}
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-slate-600 transition-colors hover:text-slate-900"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>홈으로</span>
          </Link>
        </div>

        {/* 헤더 */}
        <header className="mb-8">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
              <BookOpen className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">강의 목록</h1>
              <p className="mt-1 text-sm text-slate-500">
                수강할 강의를 선택하세요
              </p>
            </div>
          </div>

          {/* 검색 및 필터 */}
          <div className="mb-6 space-y-4">
            {/* 검색 바 */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="강의 제목 또는 강사명으로 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm shadow-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* 필터 섹션 */}
            <div className="space-y-4">
              {/* 과목 종류 필터 (선생님의 세부분야) */}
              {specializations.length > 0 && (
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">
                    과목 종류
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => setSpecializationFilter("all")}
                      className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                        specializationFilter === "all"
                          ? "bg-blue-600 text-white hover:bg-blue-700"
                          : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                      }`}
                    >
                      전체
                    </button>
                    {specializations.map((specialization) => (
                      <button
                        key={specialization}
                        onClick={() => setSpecializationFilter(specialization)}
                        className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                          specializationFilter === specialization
                            ? "bg-blue-600 text-white hover:bg-blue-700"
                            : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                        }`}
                      >
                        {specialization}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* 카테고리 필터 (개념강의 등) */}
              {categories.length > 0 && (
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">
                    카테고리
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => setCategoryFilter("all")}
                      className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                        categoryFilter === "all"
                          ? "bg-blue-600 text-white hover:bg-blue-700"
                          : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                      }`}
                    >
                      전체
                    </button>
                    {categories.map((category) => (
                      <button
                        key={category}
                        onClick={() => setCategoryFilter(category)}
                        className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                          categoryFilter === category
                            ? "bg-blue-600 text-white hover:bg-blue-700"
                            : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                        }`}
                      >
                        {category}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* 필터 초기화 및 결과 개수 */}
              {hasActiveFilters && (
                <div className="flex items-center gap-3">
                  <button
                    onClick={resetFilters}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 transition-colors hover:bg-slate-50"
                  >
                    <X className="h-4 w-4" />
                    <span>필터 초기화</span>
                  </button>
                  {filteredCourses.length !== courses.length && (
                    <span className="text-sm text-slate-600">
                      {filteredCourses.length}개 / 전체 {courses.length}개
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </header>

      {isLoading && (
        <div className="flex flex-col items-center justify-center gap-4 py-16">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="text-sm text-slate-600">강의 목록을 불러오는 중...</span>
        </div>
      )}


      {!isLoading && !error && (
        <>
          {courses.length === 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-sm">
              <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                <BookOpen className="h-8 w-8" />
              </div>
              <h3 className="mb-2 text-lg font-semibold text-slate-900">등록된 강의가 없습니다</h3>
              <p className="mb-6 text-sm text-slate-600">
                {isInstructor ? "새로운 강의를 업로드하여 시작하세요" : "강의가 업로드되면 여기에 표시됩니다"}
              </p>
            </div>
          ) : filteredCourses.length === 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-sm">
              <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                <Search className="h-8 w-8" />
              </div>
              <h3 className="mb-2 text-lg font-semibold text-slate-900">
                검색 결과가 없습니다
              </h3>
              <p className="mb-6 text-sm text-slate-600">
                다른 검색어나 필터를 시도해보세요
              </p>
              {hasActiveFilters && (
                <button
                  onClick={resetFilters}
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                >
                  <X className="h-4 w-4" />
                  <span>필터 초기화</span>
                </button>
              )}
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredCourses.map((course) => (
                <div
                  key={course.id}
                  className={`group relative rounded-2xl border bg-white p-6 shadow-sm transition-all hover:shadow-lg ${
                    course.status === "completed"
                      ? "border-slate-200 hover:border-blue-300"
                      : course.status === "processing"
                      ? "border-yellow-200 bg-yellow-50/50"
                      : "border-red-200 bg-red-50/50"
                  }`}
                >
                  {/* 삭제 버튼 */}
                  <button
                    onClick={(e) => handleDelete(course.id, e)}
                    disabled={deletingCourseId === course.id}
                    className="absolute top-4 right-4 rounded-lg bg-red-100 p-2 text-red-600 transition-colors hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="강의 삭제"
                  >
                    {deletingCourseId === course.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </button>
                  
                  <div
                    onClick={(e) => {
                      // 삭제 버튼 클릭 시에는 동작 안 함
                      if ((e.target as HTMLElement).closest('button')) {
                        return;
                      }
                      // 완료된 강의만 클릭 가능
                      if (course.status === "completed" && course.instructor_id) {
                        router.push(`/student/courses/${course.instructor_id}/${course.id}/chapters`);
                      }
                    }}
                    className={`${
                      course.status === "completed" && course.instructor_id
                        ? "cursor-pointer"
                        : "cursor-default"
                    }`}
                  >
                    {/* 상태 배지 */}
                    <div className="mb-4 flex items-center justify-between">
                      {getStatusBadge(course.status)}
                    </div>

                    {/* 강의 제목 */}
                    <h3 className="mb-3 text-lg font-semibold text-slate-900 transition-colors group-hover:text-blue-600 line-clamp-2 pr-8">
                      {course.title || course.id}
                    </h3>

                    {/* 강사명 */}
                    {course.instructor_name && (
                      <div className="mb-3 flex items-center gap-2 text-sm text-slate-600">
                        <User className="h-4 w-4 text-slate-400" />
                        <span className="font-medium">{course.instructor_name} 선생님</span>
                      </div>
                    )}

                    {/* 강의 정보 */}
                    <div className="space-y-2.5 border-t border-slate-100 pt-4">
                      {course.category && (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <BookOpen className="h-4 w-4 text-slate-400" />
                          <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                            {course.category}
                          </span>
                        </div>
                      )}
                      {course.created_at && (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <Clock className="h-4 w-4 text-slate-400" />
                          <span>{new Date(course.created_at).toLocaleDateString("ko-KR")}</span>
                      </div>
                    )}
                      {course.status === "processing" && (
                        <div className="flex items-center gap-2 text-sm text-yellow-700">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>진행률: {course.progress}%</span>
                      </div>
                    )}
                  </div>

                    {/* 액션 버튼 */}
                  {course.status === "completed" && (
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          // instructor_id가 있으면 챕터 페이지로 이동
                          if (course.instructor_id) {
                            router.push(`/student/courses/${course.instructor_id}/${course.id}/chapters`);
                          }
                        }}
                        className="mt-4 w-full flex items-center justify-between rounded-lg bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100"
                      >
                        <span>수강하기</span>
                        <PlayCircle className="h-4 w-4" />
                      </button>
                  )}

                  {course.status === "processing" && (
                      <div className="mt-4 rounded-lg bg-yellow-50 px-4 py-2.5 text-sm text-yellow-700">
                        <div className="flex items-center gap-2">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>처리 중입니다</span>
                      </div>
                    </div>
                  )}

                  {course.status === "failed" && (
                      <div className="mt-4 rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-700">
                        <div className="flex items-center gap-2">
                          <XCircle className="h-4 w-4" />
                          <span>처리 실패</span>
                      </div>
                    </div>
                  )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
      </div>
    </main>
  );
}

