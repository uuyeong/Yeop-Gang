"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  BookOpen,
  Clock,
  Trash2,
  Upload,
  CheckCircle2,
  Loader2,
  XCircle,
  AlertCircle,
  Plus,
  Edit2,
  X,
} from "lucide-react";
import { apiGet, apiDelete, apiPatch, apiPost, handleApiError } from "../../../lib/api";

type Course = {
  id: string;
  title: string;
  category?: string;
  status: string;
  created_at?: string;
  progress: number;
  instructor_name?: string;
  has_chapters?: boolean;
  chapter_count?: number;
  total_chapters?: number;
};

export default function InstructorCoursesPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingCourseId, setDeletingCourseId] = useState<string | null>(null);
  const [instructorId, setInstructorId] = useState<string | null>(null);
  const [instructorName, setInstructorName] = useState<string | null>(null);
  const [editingCourseId, setEditingCourseId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [showCreateCourseModal, setShowCreateCourseModal] = useState(false);
  const [newCourseId, setNewCourseId] = useState("");
  const [newCourseTitle, setNewCourseTitle] = useState("");
  const [newCourseCategory, setNewCourseCategory] = useState("");
  const [newTotalChapters, setNewTotalChapters] = useState<number | "">("");

  useEffect(() => {
    // 로그인 확인 (새 인증 시스템 우선, 구 시스템 fallback)
    if (typeof window !== "undefined") {
      // 새 인증 시스템 확인
      const { isAuthenticated, getUser, getToken } = require("../../../lib/auth");
      const token = getToken();
      const user = getUser();
      
      if (token && isAuthenticated() && user?.role === "instructor") {
        setInstructorId(user.id);
        fetchCourses(token);
        return;
      }
      
      // 구 시스템 fallback
      const oldId = localStorage.getItem("instructor_id");
      const oldToken = localStorage.getItem("instructor_token");
      
      if (oldId && oldToken) {
        setInstructorId(oldId);
        fetchCourses(oldToken);
        return;
      }
      
      // 인증되지 않은 경우 홈으로 이동
      router.push("/");
    }
  }, [router]);

  const fetchCourses = async (token: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiGet<Course[]>("/api/instructor/courses", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setCourses(data);
      
      // 강사명 가져오기 (첫 번째 강의에서)
      if (data.length > 0 && data[0].instructor_name) {
        setInstructorName(data[0].instructor_name);
      } else {
        // 강사명이 없으면 사용자 정보에서 가져오기
        const { getUser } = require("../../../lib/auth");
        const user = getUser();
        if (user?.name) {
          setInstructorName(user.name);
        }
      }
    } catch (err) {
      console.error("강의 목록 조회 오류:", err);
      const apiError = handleApiError(err);
      setError(apiError.message);
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
      // 새 인증 시스템 우선, 구 시스템 fallback
      const { getToken, isAuthenticated } = require("../../../lib/auth");
      let token = getToken();
      
      if (!token || !isAuthenticated()) {
        token = typeof window !== "undefined" ? localStorage.getItem("instructor_token") : null;
      }
      
      if (!token) {
        throw new Error("로그인이 필요합니다.");
      }

      await apiDelete(`/api/instructor/courses/${courseId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
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

  const handleRefresh = () => {
    // 새 인증 시스템 우선, 구 시스템 fallback
    if (typeof window !== "undefined") {
      const { getToken, isAuthenticated } = require("../../../lib/auth");
      const token = getToken();
      
      if (token && isAuthenticated()) {
        fetchCourses(token);
        return;
      }
      
      const oldToken = localStorage.getItem("instructor_token");
      if (oldToken) {
        fetchCourses(oldToken);
      }
    }
  };

  const handleEdit = (course: Course) => {
    setEditingCourseId(course.id);
    setEditTitle(course.title || "");
    setEditCategory(course.category || "");
  };

  const handleSaveEdit = async (courseId: string) => {
    try {
      // 새 인증 시스템 우선, 구 시스템 fallback
      const { getToken, isAuthenticated } = require("../../../lib/auth");
      let token = getToken();
      
      if (!token || !isAuthenticated()) {
        token = typeof window !== "undefined" ? localStorage.getItem("instructor_token") : null;
      }
      
      if (!token) {
        throw new Error("로그인이 필요합니다.");
      }

      await apiPatch(
        `/api/instructor/courses/${courseId}`,
        {
          title: editTitle.trim() || null,
          category: editCategory.trim() || null,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setEditingCourseId(null);
      handleRefresh();
    } catch (err) {
      console.error("강의 수정 오류:", err);
      const apiError = handleApiError(err);
      alert(`강의 수정 실패: ${apiError.message}`);
    }
  };

  const handleCancelEdit = () => {
    setEditingCourseId(null);
    setEditTitle("");
    setEditCategory("");
  };


  const handleCreateCourse = async () => {
    // 과목 필수 검증
    if (!newCourseCategory || !newCourseCategory.trim()) {
      alert("과목을 입력하세요.");
      return;
    }
    if (!newCourseId.trim()) {
      alert("강의 목록 ID를 입력하세요.");
      return;
    }
    if (!newCourseTitle.trim()) {
      alert("강의명을 입력하세요.");
      return;
    }
    if (newTotalChapters === "" || newTotalChapters === null || newTotalChapters === undefined) {
      alert("전체 강의 수를 입력하세요.");
      return;
    }

    try {
      // 새 인증 시스템 우선, 구 시스템 fallback
      const { getToken, isAuthenticated } = require("../../../lib/auth");
      let token = getToken();
      
      if (!token || !isAuthenticated()) {
        token = typeof window !== "undefined" ? localStorage.getItem("instructor_token") : null;
      }
      
      if (!token) {
        throw new Error("로그인이 필요합니다.");
      }

      await apiPost(
        `/api/instructor/courses`,
        {
          course_id: newCourseId.trim(),
          title: newCourseTitle.trim(),
          category: newCourseCategory.trim() || null,
          total_chapters: Number(newTotalChapters),
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // 모달 닫기 및 폼 초기화
      setShowCreateCourseModal(false);
      setNewCourseId("");
      setNewCourseTitle("");
      setNewCourseCategory("");
      setNewTotalChapters("");
      
      // 목록 새로고침
      handleRefresh();
    } catch (err) {
      console.error("강의 생성 오류:", err);
      const apiError = handleApiError(err);
      alert(`강의 목록 생성 실패: ${apiError.message}`);
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
        <header className="mb-6 sm:mb-8">
          <div className="mb-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
            <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
              <div className="flex h-8 w-8 sm:h-10 sm:w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600 flex-shrink-0">
                <BookOpen className="h-4 w-4 sm:h-5 sm:w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-slate-900">내 강의 관리</h1>
                <div className="mt-0.5 sm:mt-1">
                  <p className="text-xs sm:text-sm text-slate-500">
                    {instructorName ? (
                      <>
                        <span className="font-medium text-slate-700">{instructorName} 선생님</span>
                        {instructorId && (
                          <span className="text-slate-400"> ({instructorId})</span>
                        )}
                      </>
                    ) : (
                      instructorId && `강사 ID: ${instructorId}`
                    )}
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
              <button
                onClick={handleRefresh}
                className="flex-1 sm:flex-none rounded-lg border border-slate-300 bg-white px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium text-slate-700 transition-colors hover:border-blue-500 hover:bg-blue-50 whitespace-nowrap"
              >
                새로고침
              </button>
              <button
                onClick={() => setShowCreateCourseModal(true)}
                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 sm:gap-2 rounded-lg bg-blue-600 px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium text-white transition-colors hover:bg-blue-700 whitespace-nowrap"
              >
                <Plus className="h-3 w-3 sm:h-4 sm:w-4" />
                <span className="hidden sm:inline">강의 목록 생성</span>
                <span className="sm:hidden">생성</span>
              </button>
            </div>
          </div>
        </header>

        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-4 py-16">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="text-sm text-slate-600">강의 목록을 불러오는 중...</span>
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
              onClick={handleRefresh}
              className="w-full rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
            >
              다시 시도
            </button>
          </div>
        )}

        {!isLoading && !error && (
          <>
            {courses.length === 0 ? (
              <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-sm">
                <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                  <BookOpen className="h-8 w-8" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-slate-900">
                  등록된 강의가 없습니다
                </h3>
                <p className="mb-6 text-sm text-slate-600">
                  새로운 강의를 업로드하여 시작하세요
                </p>
                <Link
                  href="/"
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                >
                  <ArrowLeft className="h-4 w-4" />
                  <span>홈으로</span>
                </Link>
              </div>
            ) : (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {courses.map((course) => (
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
                    {/* 수정/삭제 버튼 */}
                    <div className="absolute top-4 right-4 flex gap-2">
                      {editingCourseId === course.id ? (
                        <>
                          <button
                            onClick={() => handleSaveEdit(course.id)}
                            className="rounded-lg bg-green-100 p-2 text-green-600 transition-colors hover:bg-green-200"
                            title="저장"
                          >
                            <CheckCircle2 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="rounded-lg bg-slate-100 p-2 text-slate-600 transition-colors hover:bg-slate-200"
                            title="취소"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => handleEdit(course)}
                            className="rounded-lg bg-blue-100 p-2 text-blue-600 transition-colors hover:bg-blue-200"
                            title="강의 수정"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={(e) => handleDelete(course.id, e)}
                            disabled={deletingCourseId === course.id}
                            className="rounded-lg bg-red-100 p-2 text-red-600 transition-colors hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="강의 삭제"
                          >
                            {deletingCourseId === course.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </button>
                        </>
                      )}
                    </div>

                    {/* 상태 배지 */}
                    <div className="mb-4 flex items-center justify-between">
                      {getStatusBadge(course.status)}
                    </div>

                    {/* 강의 제목 (수정 모드) */}
                    {editingCourseId === course.id ? (
                      <div className="mb-3 space-y-2 pr-8">
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          placeholder="강의명"
                          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                        />
                        <input
                          type="text"
                          value={editCategory}
                          onChange={(e) => setEditCategory(e.target.value)}
                          placeholder="과목"
                          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                        />
                      </div>
                    ) : (
                      <>
                        <h3 className="mb-3 text-lg font-semibold text-slate-900 transition-colors group-hover:text-blue-600 line-clamp-2 pr-8">
                          {course.title || course.id}
                        </h3>
                        {course.category && (
                          <p className="mb-2 text-xs text-slate-500 pr-8">
                            과목: {course.category}
                          </p>
                        )}
                      </>
                    )}

                    {/* 강의 정보 */}
                    <div className="space-y-2.5 border-t border-slate-100 pt-4">
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

                    {/* 과목 */}
                    {course.category && (
                      <p className="mb-2 text-xs text-slate-500">
                        과목: {course.category}
                      </p>
                    )}

                    {/* 챕터 개수 표시 */}
                    {course.total_chapters ? (
                      <div className="mt-2 text-xs text-slate-500">
                        등록된 강의의: {course.chapter_count ?? 0}/{course.total_chapters}
                      </div>
                    ) : course.chapter_count !== undefined ? (
                      <div className="mt-2 text-xs text-slate-500">
                        등록된 강의의: {course.chapter_count}개
                      </div>
                    ) : null}

                    {/* 액션 버튼 */}
                    <div className="mt-4 flex gap-2">
                      {course.status === "completed" && (
                        <Link
                          href={`/instructor/courses/${course.id}/chapters`}
                          className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 transition-colors group-hover:bg-blue-100"
                        >
                          <span>강의 관리</span>
                          <BookOpen className="h-4 w-4" />
                        </Link>
                      )}
                    </div>

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
                ))}
              </div>
            )}
          </>
        )}

        {/* 강의 목록 생성 모달 */}
        {showCreateCourseModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-[80%] sm:w-full sm:max-w-md rounded-2xl border border-slate-200 bg-white p-4 sm:p-6 shadow-xl">
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-xl font-bold text-slate-900">강의 목록 생성</h2>
                <button
                  onClick={() => {
                    setShowCreateCourseModal(false);
                    setNewCourseId("");
                    setNewCourseTitle("");
                    setNewCourseCategory("");
                    setNewTotalChapters("");
                  }}
                  className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">
                    강의 목록 ID <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={newCourseId}
                    onChange={(e) => setNewCourseId(e.target.value)}
                    placeholder="예: Biology-Concept"
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    autoFocus
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    강의 목록을 식별하는 고유 ID입니다.
                  </p>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">
                    강의명 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={newCourseTitle}
                    onChange={(e) => setNewCourseTitle(e.target.value)}
                    placeholder="예: 생명과학1 개념강의"
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    required
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    학생들에게 표시될 강의명입니다.
                  </p>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">
                    전체 강의 수 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    value={newTotalChapters}
                    onChange={(e) => {
                      const val = e.target.value;
                      setNewTotalChapters(val === "" ? "" : parseInt(val, 10));
                    }}
                    placeholder="예: 10"
                    min="1"
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    required
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    이 강의 목록에 포함될 전체 강의 수입니다. (참고용)
                  </p>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">
                    강의 과목 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={newCourseCategory}
                    onChange={(e) => setNewCourseCategory(e.target.value)}
                    placeholder="예: 영어, 수학, 국어"
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    required
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    과목을 입력하세요. 검색 및 필터링에 사용됩니다.
                  </p>
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => {
                    setShowCreateCourseModal(false);
                    setNewCourseId("");
                    setNewCourseTitle("");
                    setNewCourseCategory("");
                    setNewTotalChapters("");
                  }}
                  className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                >
                  취소
                </button>
                <button
                  onClick={handleCreateCourse}
                  className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                >
                  생성하기
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

