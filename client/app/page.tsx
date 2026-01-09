"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, Upload, GraduationCap, PlayCircle } from "lucide-react";
import { isAuthenticated, getUser } from "@/lib/auth";

export default function Home() {
  const [isInstructor, setIsInstructor] = useState(false);

  useEffect(() => {
    // 인증 상태 확인 및 강사 여부 체크
    if (isAuthenticated()) {
      const user = getUser();
      setIsInstructor(user?.role === "instructor");
    } else {
      setIsInstructor(false);
    }

    // storage 이벤트 리스너 (다른 탭에서 로그인/로그아웃 시 동기화)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "yeopgang_access_token" || e.key === "yeopgang_user") {
        if (isAuthenticated()) {
          const user = getUser();
          setIsInstructor(user?.role === "instructor");
        } else {
          setIsInstructor(false);
        }
      }
    };

    window.addEventListener("storage", handleStorageChange);
    
    return () => {
      window.removeEventListener("storage", handleStorageChange);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="mx-auto max-w-6xl px-6 py-16">
        {/* 메인 타이틀 */}
        <div className="mb-16 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-blue-100 px-4 py-1.5 text-sm font-medium text-blue-700">
            <BookOpen className="h-4 w-4" />
            <span>옆강</span>
          </div>
          <h1 className="mb-4 text-5xl font-bold text-slate-900">
            MAIN 페이지
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-slate-600">
            강의 영상을 시청하고 AI 튜터와 실시간으로 질문하며 학습하세요.
          </p>
        </div>

        {/* 메인 액션 버튼 - 학생 중심 */}
        <div className="mb-20 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          {/* 강사 로그인 시에만 강의 업로드 버튼 표시 */}
          {isInstructor && (
            <Link
              href="/instructor/upload"
              className="group flex items-center gap-3 rounded-xl bg-blue-600 px-8 py-4 text-base font-semibold text-white shadow-lg transition-all hover:bg-blue-700 hover:shadow-xl"
            >
              <Upload className="h-5 w-5" />
              <span>강의 업로드</span>
            </Link>
          )}
          <Link
            href="/student"
            className="group flex items-center gap-3 rounded-xl border-2 border-slate-300 bg-white px-8 py-4 text-base font-semibold text-slate-700 transition-all hover:border-blue-500 hover:bg-blue-50"
          >
            <GraduationCap className="h-5 w-5" />
            <span>강의 목록 보기</span>
          </Link>
        </div>

        {/* 기능 소개 */}
        <div className="grid gap-6 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
              <PlayCircle className="h-6 w-6" />
            </div>
            <h3 className="mb-2 text-lg font-semibold text-slate-900">
              강의 시청
            </h3>
            <p className="text-sm text-slate-600">
              업로드된 강의 영상을 시청하고, 타임라인을 통해 원하는 구간으로 바로 이동할 수 있습니다.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 text-green-600">
              <BookOpen className="h-6 w-6" />
            </div>
            <h3 className="mb-2 text-lg font-semibold text-slate-900">
              AI 튜터 채팅
            </h3>
            <p className="text-sm text-slate-600">
              강의 내용에 대해 실시간으로 질문하고 답변을 받을 수 있습니다. 강사의 말투로 답변합니다.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
              <GraduationCap className="h-6 w-6" />
            </div>
            <h3 className="mb-2 text-lg font-semibold text-slate-900">
              학습 도구
            </h3>
            <p className="text-sm text-slate-600">
              자동 생성된 요약노트와 퀴즈를 통해 학습 내용을 효과적으로 복습할 수 있습니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

