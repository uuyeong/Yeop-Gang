"use client";

/**
 * Design Philosophy: Neo-Brutalism Meets Korean EdTech
 * - Chunky black borders (3px)
 * - Bold typography with Black Han Sans
 * - High contrast colors: cyan, magenta, purple
 */

import { Search, User } from "lucide-react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { isAuthenticated, getUser } from "@/lib/auth";
import LoginModal from "./LoginModal";
import RegisterModal from "./RegisterModal";

export default function YeopgangHeader() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<{ id?: string; name?: string; role?: string } | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  
  // 강의 재생 페이지, 챕터 목록 페이지, 강사 페이지에서는 네비게이션 숨기기
  const isPlayPage = pathname?.startsWith('/student/play/');
  const isChaptersPage = pathname?.includes('/chapters');
  const isInstructorPage = pathname?.startsWith('/instructor/');
  const shouldHideNav = isPlayPage || isChaptersPage || isInstructorPage;

  useEffect(() => {
    setMounted(true);
    setAuthenticated(isAuthenticated());
    setUser(getUser());
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLoginSuccess = () => {
    setShowLoginModal(false);
    setAuthenticated(isAuthenticated());
    setUser(getUser());
    window.location.reload();
  };

  const handleRegisterSuccess = () => {
    setShowRegisterModal(false);
    setAuthenticated(isAuthenticated());
    setUser(getUser());
    window.location.reload();
  };

  return (
    <header className="bg-white border-b border-gray-400 sticky top-0 z-50 shadow-none">
      {/* Top Bar */}
      <div className="bg-gray-100 text-gray-700 py-2">
        <div className="container flex justify-between items-center text-sm">
          <div className="flex gap-4">
            <button className="hover:text-primary transition-all duration-100">예비고3</button>
            <button className="hover:text-primary transition-all duration-100">예비고2</button>
            <button className="hover:text-primary transition-all duration-100">예비고1</button>
            <button className="hover:text-primary transition-all duration-100">대학생</button>
          </div>
          <div className="flex gap-4">
            {mounted && authenticated ? (
              <>
                <span className="text-sm">{user?.name || user?.id}</span>
                {user?.role === "instructor" && (
                  <Link href="/instructor/courses" className="hover:text-primary transition-all duration-100">
                    강의 관리
                  </Link>
                )}
                <button 
                  onClick={() => {
                    localStorage.removeItem("yeopgang_access_token");
                    localStorage.removeItem("yeopgang_user");
                    router.push("/");
                  }}
                  className="hover:text-primary transition-all duration-100"
                >
                  로그아웃
                </button>
              </>
            ) : (
              <>
                <button 
                  onClick={() => setShowLoginModal(true)}
                  className="hover:text-primary transition-all duration-100"
                >
                  로그인
                </button>
                <button 
                  onClick={() => setShowRegisterModal(true)}
                  className="hover:text-primary transition-all duration-100"
                >
                  회원가입
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Main Header */}
      <div className="bg-white py-4">
        <div className="container flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-8">
            <Link href="/">
              <h1 className="text-3xl font-bold text-blue-500" style={{ fontFamily: 'var(--font-display)' }}>
                옆강
              </h1>
            </Link>
          </div>

          {/* Search Bar */}
          <div className="flex-1 max-w-xl mx-8">
            <div className="relative">
              <input
                type="text"
                placeholder="통합 검색"
                className="w-full px-4 py-3 border border-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-150"
              />
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <button
              className="border border-gray-400 rounded-lg p-2 hover:bg-primary hover:text-white transition-all duration-150"
              onClick={() => router.push(authenticated ? "/" : "/")}
            >
              <User size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Navigation */}
      {!shouldHideNav && (
        <nav className={`bg-white text-gray-900 pt-4 pb-3 transition-all duration-300 ${isScrolled ? 'hidden' : 'block'}`} style={{ borderBottom: '0.5px solid #9ca3af' }}>
        <div className="container">
          <ul className="flex items-center justify-center gap-12 font-medium text-lg">
            <li>
              <Link href="/student/courses" className="hover:text-primary transition-all duration-100">
                강의 목록
              </Link>
            </li>
            <li>
              <button className="hover:text-primary transition-all duration-100">수능·내신</button>
            </li>
            <li>
              <button className="hover:text-primary transition-all duration-100">대학별고사</button>
            </li>
            <li>
              <button className="hover:text-primary transition-all duration-100">입시정보</button>
            </li>
            <li>
              <button className="hover:text-primary transition-all duration-100">문제은행</button>
            </li>
            <li>
              <button className="hover:text-primary transition-all duration-100">옆강패스</button>
            </li>
          </ul>
        </div>
      </nav>
      )}
      
      {/* Login/Register Modals */}
      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onSuccess={handleLoginSuccess}
        />
      )}
      {showRegisterModal && (
        <RegisterModal
          onClose={() => setShowRegisterModal(false)}
          onSuccess={handleRegisterSuccess}
        />
      )}
    </header>
  );
}

