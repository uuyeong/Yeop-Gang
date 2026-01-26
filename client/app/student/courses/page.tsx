"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, GraduationCap, User, AlertCircle, Loader2, BookOpen, Search, Filter, ChevronDown, ChevronUp } from "lucide-react";
import { apiGet, handleApiError } from "../../../lib/api";

type Course = {
  id: string;
  title: string;
  category?: string;
  status: string;
  instructor_id: string;
  instructor_name?: string;
  instructor_profile_image_url?: string | null;
  instructor_specialization?: string | null;
  instructor_bio?: string | null;
  created_at?: string;
  progress: number;
};

type InstructorInfo = {
  id: string;
  name?: string;
  profile_image_url?: string | null;
  specialization?: string | null;
  bio?: string | null;
  courseCount: number;
};

export default function StudentCoursesPage() {
  const router = useRouter();
  const [instructors, setInstructors] = useState<InstructorInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [categories, setCategories] = useState<string[]>([]);
  const [expandedBios, setExpandedBios] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchInstructors();
  }, []);

  const fetchInstructors = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append("q", searchQuery);
      if (selectedCategory) params.append("category", selectedCategory);
      
      const courses = await apiGet<Course[]>(`/api/courses?${params.toString()}`);
      
      // 과목 목록 추출
      const categorySet = new Set<string>();
      courses.forEach((course) => {
        if (course.category) {
          categorySet.add(course.category);
        }
      });
      setCategories(Array.from(categorySet).sort());
      
      // instructor_id별로 그룹화 (이름, 프로필 사진, 전문 분야, 자기소개도 함께 저장)
      const instructorMap = new Map<string, { 
        count: number; 
        name?: string; 
        profile_image_url?: string | null;
        specialization?: string | null;
        bio?: string | null;
      }>();
      courses.forEach((course) => {
        const existing = instructorMap.get(course.instructor_id) || { 
          count: 0, 
          name: undefined,
          profile_image_url: undefined,
          specialization: undefined,
          bio: undefined,
        };
        instructorMap.set(course.instructor_id, {
          count: existing.count + 1,
          name: course.instructor_name || existing.name,
          profile_image_url: course.instructor_profile_image_url || existing.profile_image_url,
          specialization: course.instructor_specialization || existing.specialization,
          bio: course.instructor_bio || existing.bio,
        });
      });

      // 강사 정보 배열로 변환
      const instructorList: InstructorInfo[] = Array.from(instructorMap.entries()).map(
        ([id, info]) => ({
          id,
          name: info.name,
          profile_image_url: info.profile_image_url,
          specialization: info.specialization,
          bio: info.bio,
          courseCount: info.count,
        })
      );

      // 강의 수가 많은 순으로 정렬
      instructorList.sort((a, b) => b.courseCount - a.courseCount);
      setInstructors(instructorList);
    } catch (err) {
      console.error("강사 목록 조회 오류:", err);
      const apiError = handleApiError(err);
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInstructors();
  }, [searchQuery, selectedCategory]);

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
              <GraduationCap className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">강사 선택</h1>
              <p className="mt-1 text-sm text-slate-500">
                강의를 수강할 강사를 선택하세요
              </p>
            </div>
          </div>
          
          {/* 검색 및 필터 */}
          <div className="flex flex-col gap-4 sm:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="강사명 또는 강의명으로 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white pl-10 pr-4 py-2.5 text-sm text-slate-900 outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
            <div className="relative sm:w-48">
              <Filter className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full appearance-none rounded-lg border border-slate-300 bg-white pl-10 pr-8 py-2.5 text-sm text-slate-900 outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="">전체 과목</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </header>

        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-4 py-16">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="text-sm text-slate-600">강사 목록을 불러오는 중...</span>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6">
            <div className="mb-4 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-600" />
              <div className="flex-1">
                <h3 className="mb-1 text-sm font-semibold text-red-900">오류 발생</h3>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
            <button
              onClick={fetchInstructors}
              className="w-full rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
            >
              다시 시도
            </button>
          </div>
        )}

        {!isLoading && !error && (
          <>
            {instructors.length === 0 ? (
              <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-sm">
                <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                  <BookOpen className="h-8 w-8" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-slate-900">
                  등록된 강사가 없습니다
                </h3>
                <p className="text-sm text-slate-600">
                  강의가 업로드되면 강사 목록이 표시됩니다
                </p>
              </div>
            ) : (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {instructors.map((instructor) => (
                  <Link
                    key={instructor.id}
                    href={`/student/courses/${instructor.id}`}
                    className="group rounded-2xl border border-slate-200 bg-white p-4 sm:p-6 shadow-sm transition-all hover:border-blue-300 hover:shadow-lg flex flex-col max-w-sm mx-auto w-full"
                  >
                    {/* 프로필 사진 - 상단에 네모 형태로 */}
                    <div className="mb-4 relative w-full aspect-square max-w-[200px] mx-auto">
                      <img
                        src={instructor.profile_image_url || "https://i.ibb.co/27yY0pLS/default-profile.png"}
                        alt={instructor.name || "강사"}
                        className="w-full h-full rounded-lg object-cover border-2 border-slate-200"
                      />
                    </div>
                    
                    {/* 선생님 정보 */}
                    <div className="flex-1 flex flex-col text-center">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <h3 className="text-lg sm:text-xl font-semibold text-slate-900 transition-colors group-hover:text-blue-600">
                          {instructor.name ? `${instructor.name} 선생님` : "강사"}
                        </h3>
                        {instructor.bio && (
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              setExpandedBios((prev) => {
                                const newSet = new Set(prev);
                                if (newSet.has(instructor.id)) {
                                  newSet.delete(instructor.id);
                                } else {
                                  newSet.add(instructor.id);
                                }
                                return newSet;
                              });
                            }}
                            className="flex items-center gap-0.5 text-xs text-blue-600 hover:text-blue-700 transition-colors"
                          >
                            {expandedBios.has(instructor.id) ? (
                              <ChevronUp className="h-3.5 w-3.5" />
                            ) : (
                              <ChevronDown className="h-3.5 w-3.5" />
                            )}
                          </button>
                        )}
                      </div>
                      <div className="flex items-center justify-center gap-2 sm:gap-3 mb-2">
                        {instructor.specialization && (
                          <p className="text-sm sm:text-base text-blue-600 font-medium">
                            {instructor.specialization}
                          </p>
                        )}
                        {instructor.specialization && (
                          <span className="text-slate-400">•</span>
                        )}
                        <p className="text-sm sm:text-base text-slate-600">
                          {instructor.courseCount}개 강의
                        </p>
                      </div>
                      {instructor.bio && expandedBios.has(instructor.id) && (
                        <p className="text-xs sm:text-sm text-slate-500 mb-0">
                          {instructor.bio}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center justify-between rounded-lg bg-blue-50 px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm font-medium text-blue-700 transition-colors group-hover:bg-blue-100 mt-4">
                      <span>강의 보기</span>
                      <BookOpen className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
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
