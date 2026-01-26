"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Search, BookOpen, User } from "lucide-react";
import { apiGet } from "@/lib/api";

type Course = {
  id: string;
  title: string;
  category?: string;
  instructor_id: string;
  instructor_name?: string;
  status: string;
};

export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (query) {
      performSearch(query);
    }
  }, [query]);

  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setCourses([]);
      return;
    }

    setIsLoading(true);
    try {
      const trimmedQuery = searchQuery.trim();
      
      // 모든 강의 가져오기
      const allCourses = await apiGet<Course[]>(`/api/courses`);
      
      // 인기 카테고리 목록에 있으면 키워드 매핑으로 필터링
      const isCategory = popularCategories.includes(trimmedQuery);
      
      let filteredCourses = allCourses;
      
      if (isCategory) {
        // 과목별 키워드 매핑
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
        
        const keywords = categoryMap[trimmedQuery] || [];
        if (keywords.length > 0) {
          filteredCourses = allCourses.filter(course => {
            const title = (course.title || "").toLowerCase();
            const category = (course.category || "").toLowerCase();
            const courseId = (course.id || "").toLowerCase();
            
            return keywords.some(keyword => 
              title.includes(keyword.toLowerCase()) ||
              category.includes(keyword.toLowerCase()) ||
              courseId.includes(keyword.toLowerCase())
            );
          });
        }
      } else {
        // 일반 검색어는 강의명, 강사명, 카테고리에서 검색
        const queryLower = trimmedQuery.toLowerCase();
        filteredCourses = allCourses.filter(course => {
          const title = (course.title || "").toLowerCase();
          const category = (course.category || "").toLowerCase();
          const instructorName = (course.instructor_name || "").toLowerCase();
          const courseId = (course.id || "").toLowerCase();
          
          return title.includes(queryLower) ||
                 category.includes(queryLower) ||
                 instructorName.includes(queryLower) ||
                 courseId.includes(queryLower);
        });
      }
      
      // 완료된 강의만 필터링
      filteredCourses = filteredCourses.filter(c => c.status === "completed");
      
      setCourses(filteredCourses);
    } catch (err) {
      console.error("검색 오류:", err);
      setCourses([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCategorySearch = (category: string) => {
    router.push(`/search?q=${encodeURIComponent(category)}`);
  };

  // 인기 검색어 (과목 목록)
  const popularCategories = [
    "국어", "수학", "영어", "사회", "한국사",
    "물리", "화학", "생명과학", "지구과학"
  ];

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-6 sm:py-10">
        {/* 인기 검색어 */}
        <div className="mb-6 sm:mb-8">
          <p className="text-xs sm:text-sm text-slate-600 mb-2">인기 검색어</p>
          <div className="flex flex-wrap gap-1.5 sm:gap-2">
            {popularCategories.map((category) => (
              <button
                key={category}
                onClick={() => handleCategorySearch(category)}
                className="px-2 sm:px-3 py-1 bg-white border-2 border-gray-300 rounded-lg text-xs sm:text-sm hover:bg-primary hover:text-white hover:border-primary transition-all duration-150"
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* 검색 결과 */}
        {query && (
          <div>
            <div className="mb-4 sm:mb-6">
              <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-slate-900">
                검색 결과: "{query}"
              </h2>
              <p className="text-xs sm:text-sm text-slate-600 mt-1">
                {isLoading ? "검색 중..." : `${courses.length}개의 강의를 찾았습니다`}
              </p>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-8 sm:py-12">
                <div className="text-slate-400 text-sm sm:text-base">검색 중...</div>
              </div>
            ) : courses.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 sm:py-12 text-slate-400">
                <Search className="h-8 w-8 sm:h-12 sm:w-12 mb-3 sm:mb-4 opacity-50" />
                <p className="text-base sm:text-lg mb-1 sm:mb-2">검색 결과가 없습니다</p>
                <p className="text-xs sm:text-sm mt-1 sm:mt-2 text-center px-4">다른 검색어를 시도해보세요</p>
              </div>
            ) : (
              <div className="grid gap-3 sm:gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                {courses.map((course) => (
                  <Link
                    key={course.id}
                    href={`/student/courses/${course.instructor_id}/${course.id}/chapters`}
                    className="group border-2 border-gray-300 rounded-lg p-3 sm:p-4 hover:border-primary hover:shadow-md transition-all duration-150 bg-white"
                  >
                    <div className="mb-2 sm:mb-3">
                      <h3 className="font-semibold text-sm sm:text-base text-slate-900 group-hover:text-primary transition-colors line-clamp-2 mb-1 sm:mb-2">
                        {course.title}
                      </h3>
                      {course.instructor_name && (
                        <div className="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm text-slate-600 mb-1 sm:mb-2">
                          <User className="h-3 w-3 flex-shrink-0" />
                          <span className="truncate">{course.instructor_name}</span>
                        </div>
                      )}
                      {course.category && (
                        <div className="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm text-slate-600">
                          <BookOpen className="h-3 w-3 flex-shrink-0" />
                          <span className="px-2 py-0.5 sm:py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium">
                            {course.category}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="mt-3 sm:mt-4 flex items-center gap-2 text-primary text-xs sm:text-sm font-medium">
                      <span>강의 보기</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 검색어가 없을 때 */}
        {!query && (
          <div className="flex flex-col items-center justify-center py-8 sm:py-12 text-slate-400">
            <Search className="h-12 w-12 sm:h-16 sm:w-16 mb-3 sm:mb-4 opacity-50" />
            <p className="text-lg sm:text-xl font-medium mb-1 sm:mb-2">검색어를 입력하세요</p>
            <p className="text-xs sm:text-sm text-center px-4">강의명, 강사명, 과목으로 검색할 수 있습니다</p>
          </div>
        )}
      </div>
    </main>
  );
}

