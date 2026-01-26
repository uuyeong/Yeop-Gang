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
  
  // 강의 재생 페이지, 챕터 목록 페이지, 강사 페이지, 마이페이지, 검색 페이지에서는 네비게이션 숨기기
  const isPlayPage = pathname?.startsWith('/student/play/');
  const isChaptersPage = pathname?.includes('/chapters');
  const isInstructorPage = pathname?.startsWith('/instructor/');
  const isMyPage = pathname?.startsWith('/mypage');
  const isSearchPage = pathname?.startsWith('/search');
  const shouldHideNav = isPlayPage || isChaptersPage || isInstructorPage || isMyPage || isSearchPage;

  useEffect(() => {
    setMounted(true);
    setAuthenticated(isAuthenticated());
    setUser(getUser());
  }, []);

  // 스크롤 시 네비게이션 바 숨기기 기능 비활성화 (항상 표시)
  // useEffect(() => {
  //   let ticking = false;
  //   
  //   const handleScroll = () => {
  //     if (!ticking) {
  //       window.requestAnimationFrame(() => {
  //         setIsScrolled(window.scrollY > 50);
  //         ticking = false;
  //       });
  //       ticking = true;
  //     }
  //   };

  //   window.addEventListener('scroll', handleScroll, { passive: true });
  //   return () => window.removeEventListener('scroll', handleScroll);
  // }, []);

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

  // 수능 D-day 계산
  const getSuneungDday = () => {
    const suneungDates = [
      { date: new Date('2026-11-19'), year: 2026 },
      { date: new Date('2027-11-18'), year: 2027 },
      { date: new Date('2028-11-16'), year: 2028 },
      { date: new Date('2029-11-15'), year: 2029 },
    ];

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // 가장 가까운 미래 수능 날짜 찾기
    const nextSuneung = suneungDates.find(item => {
      const d = new Date(item.date);
      d.setHours(0, 0, 0, 0);
      return d >= today;
    }) || suneungDates[suneungDates.length - 1]; // 모든 날짜가 지났으면 마지막 날짜 사용

    const targetDate = new Date(nextSuneung.date);
    targetDate.setHours(0, 0, 0, 0);

    const diffTime = targetDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    let ddayText = '';
    if (diffDays === 0) {
      ddayText = 'D-day';
    } else if (diffDays > 0) {
      ddayText = `D-${diffDays}`;
    } else {
      ddayText = `D+${Math.abs(diffDays)}`;
    }

    return {
      year: nextSuneung.year,
      dday: ddayText,
    };
  };

  const [suneungInfo, setSuneungInfo] = useState({ year: 2027, dday: '' });

  useEffect(() => {
    setSuneungInfo(getSuneungDday());
    // 매일 자정에 업데이트하기 위해 하루마다 체크
    const interval = setInterval(() => {
      setSuneungInfo(getSuneungDday());
    }, 1000 * 60 * 60); // 1시간마다 체크

    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-white sticky top-0 z-50 shadow-none">
      {/* Top Bar */}
      <div className="bg-gray-100 text-gray-700 py-2">
        <div className="container flex justify-between items-center text-xs sm:text-sm">
          {/* 수능 D-day - 왼쪽 */}
          <div className="text-xs sm:text-sm text-gray-700 truncate">
            <span>{suneungInfo.year} 수능 </span>
            <span className="text-blue-500 font-medium">{suneungInfo.dday}</span>
          </div>
          {mounted && authenticated ? (
            <div className="flex items-center gap-1 sm:gap-2">
              <span className="text-xs sm:text-sm text-gray-700 truncate max-w-[80px] sm:max-w-none">{user?.id}</span>
              <span className="text-gray-400">|</span>
              <button
                onClick={() => {
                  localStorage.removeItem("yeopgang_access_token");
                  localStorage.removeItem("yeopgang_user");
                  setAuthenticated(false);
                  setUser(null);
                  window.location.reload();
                }}
                className="hover:text-primary transition-all duration-100 text-xs sm:text-sm"
              >
                로그아웃
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1 sm:gap-2">
              <button
                onClick={() => setShowRegisterModal(true)}
                className="hover:text-primary transition-all duration-100 text-xs sm:text-sm"
              >
                회원가입
              </button>
              <span className="text-gray-400">|</span>
              <button
                onClick={() => setShowLoginModal(true)}
                className="hover:text-primary transition-all duration-100 text-xs sm:text-sm"
              >
                로그인
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Header */}
      <div className="bg-white py-4 sm:py-6 md:py-9" style={{ borderBottom: '0.5px solid #d1d5db' }}>
        <div className="container">
          {/* 모바일: 세로 배치, 데스크톱: 가로 배치 */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-0">
            {/* 모바일: 첫 번째 줄 (로고 + 버튼), 데스크톱: Search Bar (왼쪽) */}
            <div className="w-full sm:w-48 md:w-64 flex-shrink-0 order-1 sm:order-1">
              {/* 모바일: 첫 번째 줄 - 로고(중앙) + 버튼(오른쪽) */}
              <div className="flex sm:hidden items-center justify-between relative">
                {/* 모바일: Logo - 중앙 */}
                <div className="absolute left-1/2 -translate-x-1/2">
                  <Link href="/">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src="/image/YeopGang_Logo.png"
                      alt="옆강"
                      className="h-8 w-auto"
                    />
                  </Link>
                </div>
                {/* 모바일: Action Buttons - 오른쪽 */}
                <div className="flex items-center gap-2 ml-auto">
                  {mounted && authenticated && (
                    <>
                      {user?.role === "instructor" && (
                        <Link
                          href="/instructor/courses"
                          className="border border-gray-400 rounded-lg px-2 py-1.5 hover:bg-primary hover:text-white hover:border-transparent transition-all duration-150 text-xs whitespace-nowrap"
                        >
                          관리
                        </Link>
                      )}
                      <button
                        className="border border-gray-400 rounded-lg p-1.5 hover:bg-primary hover:text-white hover:border-transparent transition-all duration-150"
                        onClick={() => router.push("/mypage")}
                      >
                        <User size={18} />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* 데스크톱: Search Bar */}
              <form
                className="hidden sm:block"
                onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  const query = formData.get("search") as string;
                  if (query?.trim()) {
                    router.push(`/search?q=${encodeURIComponent(query.trim())}`);
                  }
                }}
              >
                <div className="relative">
                  <input
                    type="text"
                    name="search"
                    placeholder="통합 검색"
                    className="w-full px-3 py-2 text-xs sm:text-sm border border-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-150"
                  />
                  <button
                    type="submit"
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary transition-colors"
                  >
                    <Search size={16} className="sm:w-[18px] sm:h-[18px]" />
                  </button>
                </div>
              </form>
            </div>

            {/* 모바일: Search Bar (아래), 데스크톱: Logo (중앙) */}
            <div className="w-full sm:flex-1 flex justify-center order-2 sm:order-2">
              {/* 모바일: Search Bar */}
              <form
                className="block sm:hidden w-full"
                onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  const query = formData.get("search") as string;
                  if (query?.trim()) {
                    router.push(`/search?q=${encodeURIComponent(query.trim())}`);
                  }
                }}
              >
                <div className="relative">
                  <input
                    type="text"
                    name="search"
                    placeholder="통합 검색"
                    className="w-full px-3 py-2 text-xs border border-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-150"
                  />
                  <button
                    type="submit"
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary transition-colors"
                  >
                    <Search size={16} />
                  </button>
                </div>
              </form>

              {/* 데스크톱: Logo - 항상 전체 페이지 기준 가운데 */}
              <div className="hidden sm:flex justify-center">
                <Link href="/">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src="/image/YeopGang_Logo.png"
                    alt="옆강"
                    className="h-10 w-auto"
                  />
                </Link>
              </div>
            </div>

            {/* 데스크톱: Action Buttons (오른쪽) */}
            <div className="hidden sm:flex items-center gap-2 sm:gap-3 w-48 md:w-64 flex-shrink-0 justify-end order-3 sm:order-3">
              {mounted && authenticated && (
                <>
                  {user?.role === "instructor" && (
                    <Link
                      href="/instructor/courses"
                      className="border border-gray-400 rounded-lg px-2 py-1.5 sm:p-2 hover:bg-primary hover:text-white hover:border-transparent transition-all duration-150 text-xs sm:text-sm whitespace-nowrap"
                    >
                      강의 관리
                    </Link>
                  )}
                  <button
                    className="border border-gray-400 rounded-lg p-1.5 sm:p-2 hover:bg-primary hover:text-white hover:border-transparent transition-all duration-150"
                    onClick={() => router.push("/mypage")}
                  >
                    <User size={18} className="sm:w-5 sm:h-5" />
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      {!shouldHideNav && (
        <nav 
          className="bg-white text-gray-900 pt-3 sm:pt-4 md:pt-5 pb-3 sm:pb-4" 
          style={{ borderBottom: '0.5px solid #d1d5db' }}
        >
          <div className="container">
            <ul className="flex items-center justify-center gap-4 sm:gap-8 md:gap-12 font-medium text-sm sm:text-base md:text-lg">
              <li>
                <Link 
                  href="/student/courses" 
                  className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg transition-all duration-100 ${
                    pathname === '/student/courses' 
                      ? 'bg-gray-200 text-gray-900' 
                      : 'hover:text-primary'
                  }`}
                >
                  선생님
                </Link>
              </li>
              <li>
                <Link 
                  href="/student/courses/all" 
                  className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg transition-all duration-100 ${
                    pathname === '/student/courses/all' 
                      ? 'bg-gray-200 text-gray-900' 
                      : 'hover:text-primary'
                  }`}
                >
                  모든 강좌
                </Link>
              </li>
              <li>
                <Link 
                  href="/guide" 
                  className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg transition-all duration-100 ${
                    pathname === '/guide' 
                      ? 'bg-gray-200 text-gray-900' 
                      : 'hover:text-primary'
                  }`}
                >
                  이용안내
                </Link>
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

