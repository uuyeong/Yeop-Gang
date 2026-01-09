"use client";

import { useState, useEffect } from "react";
import { User, LogOut, LogIn, UserPlus } from "lucide-react";
import { isAuthenticated, getUser, removeToken } from "@/lib/auth";

type HeaderProps = {
  onLoginClick?: () => void;
  onRegisterClick?: () => void;
};

export default function Header({ onLoginClick, onRegisterClick }: HeaderProps) {
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<{ id: string; role: string; name?: string } | null>(null);

  useEffect(() => {
    checkAuth();
    
    // storage 이벤트 리스너 (다른 탭에서 로그인/로그아웃 시 동기화)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "yeopgang_access_token" || e.key === "yeopgang_user") {
        checkAuth();
      }
    };
    
    window.addEventListener("storage", handleStorageChange);
    
    return () => {
      window.removeEventListener("storage", handleStorageChange);
    };
  }, []);

  const checkAuth = () => {
    const isAuth = isAuthenticated();
    setAuthenticated(isAuth);
    if (isAuth) {
      setUser(getUser());
    } else {
      setUser(null);
    }
  };

  const handleLogout = () => {
    removeToken();
    setAuthenticated(false);
    setUser(null);
    // 페이지 새로고침하여 상태 초기화
    window.location.reload();
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-white shadow-sm border-b border-slate-200">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* 로고/제목 */}
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-slate-900">옆강</h1>
          </div>

          {/* 오른쪽 메뉴 */}
          <div className="flex items-center gap-4">
            {authenticated && user ? (
              <>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <User className="h-4 w-4" />
                  <span className="font-medium">{user.name || user.id}</span>
                  <span className="text-slate-400">({user.role === "instructor" ? "강사" : "학생"})</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                >
                  <LogOut className="h-4 w-4" />
                  <span>로그아웃</span>
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={onLoginClick}
                  className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                >
                  <LogIn className="h-4 w-4" />
                  <span>로그인</span>
                </button>
                <button
                  onClick={onRegisterClick}
                  className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                >
                  <UserPlus className="h-4 w-4" />
                  <span>회원가입</span>
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
