"use client";

import { useState, useEffect } from "react";
import { User, LogOut, LogIn, UserPlus, UserCog } from "lucide-react";
import { isAuthenticated, getUser, getToken, removeToken, saveUser } from "@/lib/auth";
import { getInstructorProfile } from "@/lib/authApi";
import EditProfileModal from "@/components/EditProfileModal";

type HeaderProps = {
  onLoginClick?: () => void;
  onRegisterClick?: () => void;
};

export default function Header({ onLoginClick, onRegisterClick }: HeaderProps) {
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<{ id: string; role: string; name?: string } | null>(null);
  const [profileImageUrl, setProfileImageUrl] = useState<string | null>(null);
  const [showEditProfileModal, setShowEditProfileModal] = useState(false);

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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- 마운트/storage 시에만 checkAuth 호출
  }, []);

  const loadProfileImage = () => {
    const currentUser = getUser();
    if (currentUser?.role === "instructor") {
      const token = getToken() || (typeof window !== "undefined" ? localStorage.getItem("instructor_token") : null);
      if (token) {
        getInstructorProfile(token)
          .then((profile) => {
            console.log("[Header] 프로필 전체:", profile);
            console.log("[Header] 프로필 이미지 URL:", profile.profile_image_url ? profile.profile_image_url.substring(0, 100) + "..." : "없음");
            if (profile.profile_image_url && profile.profile_image_url.trim()) {
              console.log("[Header] 프로필 이미지 URL 설정:", profile.profile_image_url.substring(0, 50));
              setProfileImageUrl(profile.profile_image_url);
            } else {
              console.log("[Header] 프로필 이미지 없음 - null 설정");
              setProfileImageUrl(null);
            }
          })
          .catch((e) => {
            console.error("[Header] 프로필 이미지 로드 실패:", e);
            setProfileImageUrl(null);
          });
      }
    } else {
      setProfileImageUrl(null);
    }
  };

  const checkAuth = () => {
    const isAuth = isAuthenticated();
    setAuthenticated(isAuth);
    if (isAuth) {
      const currentUser = getUser();
      setUser(currentUser);
      loadProfileImage();
    } else {
      setUser(null);
      setProfileImageUrl(null);
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
                {user.role === "instructor" && (
                  <button
                    onClick={() => setShowEditProfileModal(true)}
                    className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                  >
                    <UserCog className="h-4 w-4" />
                    <span>회원정보 수정</span>
                  </button>
                )}
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  {profileImageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element -- 동적 API URL, onError/onLoad 사용
                    <img
                      src={profileImageUrl}
                      alt="프로필"
                      className="h-8 w-8 rounded-full object-cover border border-slate-300 flex-shrink-0"
                      onError={(e) => {
                        console.error("[Header] 이미지 로드 실패 - URL:", profileImageUrl.substring(0, 100));
                        console.error("[Header] 이미지 로드 실패 - 전체 URL 길이:", profileImageUrl.length);
                        console.error("[Header] 이미지 로드 실패 - 이벤트:", e);
                        // 이미지 로드 실패 시 User 아이콘으로 대체
                        setProfileImageUrl(null);
                      }}
                      onLoad={() => {
                        console.log("[Header] ✅ 이미지 로드 성공!");
                      }}
                      style={{ display: profileImageUrl ? "block" : "none" }}
                    />
                  ) : null}
                  {!profileImageUrl && <User className="h-4 w-4 flex-shrink-0" />}
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
                {user.role === "instructor" && (
                  <EditProfileModal
                    isOpen={showEditProfileModal}
                    onClose={() => setShowEditProfileModal(false)}
                    token={getToken() || (typeof window !== "undefined" ? localStorage.getItem("instructor_token") : null) || ""}
                    onSuccess={(data) => {
                      console.log("[Header] 프로필 수정 성공 - 전체 데이터:", data);
                      console.log("[Header] 프로필 이미지 URL:", data.profile_image_url ? data.profile_image_url.substring(0, 50) + "..." : "없음");
                      const u = getUser();
                      if (u) saveUser({ ...u, name: data.name ?? u.name, email: data.email ?? u.email });
                      // 프로필 이미지 즉시 업데이트 (서버 응답에서 가져오기)
                      if (data.profile_image_url && data.profile_image_url.trim()) {
                        console.log("[Header] 프로필 이미지 URL 즉시 설정");
                        setProfileImageUrl(data.profile_image_url);
                      } else {
                        console.log("[Header] 프로필 이미지 URL 없음 - 다시 불러오기");
                        // 서버에서 다시 불러오기
                        setTimeout(() => loadProfileImage(), 500);
                      }
                      checkAuth();
                    }}
                  />
                )}
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
