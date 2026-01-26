"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { User, Settings, LogOut, Save, X, Upload, XCircle, Camera } from "lucide-react";
import { getUser, isAuthenticated, removeToken, getToken, saveUser } from "@/lib/auth";
import { updateInstructorProfile, getInstructorProfile } from "@/lib/authApi";

export default function MyPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [user, setUser] = useState<{ id?: string; name?: string; role?: string; email?: string; profile_image_url?: string | null; specialization?: string | null; bio?: string | null } | null>(null);
  const [mounted, setMounted] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  const [profileImage, setProfileImage] = useState<File | null>(null);
  const [profileImagePreview, setProfileImagePreview] = useState<string | null>(null);
  const [existingImageUrl, setExistingImageUrl] = useState<string | null>(null);
  
  // 폼 데이터
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    specialization: "",
    bio: "",
  });

  useEffect(() => {
    setMounted(true);
    const currentUser = getUser();
    if (!currentUser || !isAuthenticated()) {
      router.push("/");
      return;
    }
    setUser(currentUser);
    setFormData({
      name: currentUser.name || "",
      email: currentUser.email || "",
      specialization: "",
      bio: "",
    });

    // 강사인 경우 프로필 이미지와 최신 정보 가져오기
    if (currentUser.role === "instructor") {
      const token = getToken();
      if (token) {
        getInstructorProfile(token)
          .then((profile) => {
            // 프로필 이미지 업데이트
            if (profile.profile_image_url) {
              setExistingImageUrl(profile.profile_image_url);
              setProfileImagePreview(profile.profile_image_url);
            }
            // 사용자 정보 최신화 (이름, 이메일, 전문분야, 자기소개 포함)
            setUser((prev) => ({
              ...prev,
              name: profile.name || prev?.name,
              email: profile.email || prev?.email,
              profile_image_url: profile.profile_image_url || prev?.profile_image_url,
              specialization: profile.specialization || prev?.specialization,
              bio: profile.bio || prev?.bio,
            }));
            // formData도 업데이트
            setFormData({
              name: profile.name || "",
              email: profile.email || "",
              specialization: profile.specialization || "",
              bio: profile.bio || "",
            });
          })
          .catch((err) => {
            console.error("프로필 이미지 로드 실패:", err);
          });
      }
    }
  }, [router]);

  const handleLogout = () => {
    removeToken();
    window.location.reload();
  };

  const handleEdit = () => {
    setIsEditing(true);
    setError("");
    setSuccess("");
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError("");
    setSuccess("");
    // 원래 값으로 복원
    if (user) {
      setFormData({
        name: user.name || "",
        email: user.email || "",
        specialization: user.specialization || "",
        bio: user.bio || "",
      });
      setProfileImage(null);
      setProfileImagePreview(existingImageUrl);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith("image/")) {
        setError("이미지 파일만 업로드 가능합니다.");
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        setError("이미지 크기는 5MB 이하여야 합니다.");
        return;
      }
      setProfileImage(file);
      setError("");
      const reader = new FileReader();
      reader.onerror = () => {
        setError("이미지를 읽을 수 없습니다.");
      };
      reader.onloadend = () => {
        const result = reader.result as string;
        setProfileImagePreview(result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleImageRemove = () => {
    setProfileImage(null);
    setProfileImagePreview(null);
    setExistingImageUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleImageClick = () => {
    if (isEditing && user?.role === "instructor") {
      fileInputRef.current?.click();
    }
  };

  const handleSave = async () => {
    if (!user || user.role !== "instructor") {
      setError("프로필 수정은 강사만 가능합니다.");
      return;
    }

    const token = getToken();
    if (!token) {
      setError("인증 토큰이 없습니다.");
      return;
    }

    setIsSaving(true);
    setError("");
    setSuccess("");

    try {
      // 프로필 이미지 처리
      let profileImageUrl: string | undefined = undefined;
      if (profileImage && profileImagePreview) {
        // 새로 선택한 이미지: Base64 데이터 URL 사용
        profileImageUrl = profileImagePreview;
      } else if (existingImageUrl && !profileImage && profileImagePreview) {
        // 기존 이미지 유지 (제거하지 않은 경우)
        profileImageUrl = existingImageUrl;
      } else if (!profileImagePreview) {
        // 이미지가 제거된 경우: 빈 문자열로 설정하여 서버에서 null로 처리
        profileImageUrl = "";
      }

      // 빈 문자열도 명시적으로 보내서 서버에서 None으로 처리하도록 함
      const payload: { name?: string | null; email?: string | null; profile_image_url?: string | null; specialization?: string | null; bio?: string | null } = {};
      
      // name과 email은 항상 보냄 (빈 문자열이면 서버에서 None으로 처리)
      if (formData.name !== undefined) {
        payload.name = formData.name.trim() || null;
      }
      if (formData.email !== undefined) {
        payload.email = formData.email.trim() || null;
      }
      if (formData.specialization !== undefined) {
        payload.specialization = formData.specialization.trim() || null;
      }
      if (formData.bio !== undefined) {
        payload.bio = formData.bio.trim() || null;
      }
      if (profileImageUrl !== undefined) {
        payload.profile_image_url = profileImageUrl;
      }

      const result = await updateInstructorProfile(token, payload);

      // 저장 후 최신 프로필 정보 다시 불러오기
      const updatedProfile = await getInstructorProfile(token);

      // 서버 응답에서 업데이트된 값 사용
      const updatedUser = {
        id: user.id || "",
        role: user.role || "student",
        name: updatedProfile.name ?? null,
        email: updatedProfile.email ?? null,
        profile_image_url: updatedProfile.profile_image_url ?? null,
        specialization: updatedProfile.specialization ?? null,
        bio: updatedProfile.bio ?? null,
      };
      setUser(updatedUser);
      saveUser(updatedUser);
      
      // formData도 업데이트
      setFormData({
        name: updatedProfile.name || "",
        email: updatedProfile.email || "",
        specialization: updatedProfile.specialization || "",
        bio: updatedProfile.bio || "",
      });
      
      // 이미지 상태 업데이트
      if (updatedProfile.profile_image_url) {
        setExistingImageUrl(updatedProfile.profile_image_url);
        setProfileImagePreview(updatedProfile.profile_image_url);
      } else {
        setExistingImageUrl(null);
        setProfileImagePreview(null);
      }
      setProfileImage(null);
      
      // 프로필 사진이 업데이트되었으므로 user 상태도 갱신
      if (updatedProfile.profile_image_url) {
        setUser((prev) => ({
          ...prev,
          profile_image_url: updatedProfile.profile_image_url,
        }));
      }
      
      setSuccess("프로필이 성공적으로 수정되었습니다.");
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "프로필 수정에 실패했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  if (!mounted) {
    return null;
  }

  if (!user) {
    return null;
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="mx-auto max-w-4xl px-6 sm:px-6 py-6 sm:py-10">
        {/* 프로필 섹션 */}
        <div className="bg-white rounded-lg border-2 border-gray-300 p-4 sm:p-6 shadow-sm">
          <div className="mb-4 sm:mb-6 flex flex-row items-center justify-between gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">마이페이지</h1>
            {!isEditing && user.role === "instructor" && (
              <button
                onClick={handleEdit}
                className="flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 border-2 border-gray-300 rounded-lg hover:bg-primary hover:text-white hover:border-primary transition-all duration-150 text-sm sm:text-base"
              >
                <Settings className="h-3 w-3 sm:h-4 sm:w-4" />
                <span>수정</span>
              </button>
            )}
          </div>

          <div className="space-y-4 sm:space-y-6">
            {/* 프로필 정보 */}
            <div className="flex flex-col sm:flex-row items-start gap-4 sm:gap-6">
              {/* 프로필 사진 */}
              <div className="relative flex-shrink-0 w-full sm:w-auto flex flex-col items-center sm:items-start">
                <div
                  className={`relative flex h-20 w-20 sm:h-24 sm:w-24 items-center justify-center rounded-full overflow-hidden border-2 ${
                    isEditing && user.role === "instructor"
                      ? "border-primary cursor-pointer hover:opacity-80 transition-opacity"
                      : "border-gray-300"
                  }`}
                  onClick={handleImageClick}
                >
                  {(profileImagePreview || user.profile_image_url) ? (
                    <img
                      src={profileImagePreview || user.profile_image_url || ""}
                      alt="프로필 사진"
                      className="h-full w-full object-cover"
                      onError={(e) => {
                        // 이미지 로드 실패 시 기본 아이콘 표시
                        e.currentTarget.style.display = "none";
                        const parent = e.currentTarget.parentElement;
                        if (parent) {
                          const iconDiv = parent.querySelector(".default-icon") as HTMLElement;
                          if (iconDiv) iconDiv.style.display = "flex";
                        }
                      }}
                    />
                  ) : null}
                  <div className="default-icon flex h-full w-full items-center justify-center bg-blue-500 text-white" style={{ display: profileImagePreview || user.profile_image_url ? "none" : "flex" }}>
                    <User className="h-10 w-10 sm:h-12 sm:w-12" />
                  </div>
                  {isEditing && user.role === "instructor" && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 hover:opacity-100 transition-opacity">
                      <Camera className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
                    </div>
                  )}
                </div>
                {/* 프로필 이미지 변경/삭제 버튼 (프로필 이미지 바로 아래) */}
                {isEditing && user.role === "instructor" && (
                  <div className="mt-1.5 flex gap-1.5 justify-center">
                    <button
                      type="button"
                      onClick={handleImageClick}
                      className="px-2.5 py-1 text-xs bg-blue-500 text-white border border-blue-500 rounded hover:bg-blue-600 hover:border-blue-600 transition-all duration-150"
                    >
                      변경
                    </button>
                    {profileImagePreview && (
                      <button
                        type="button"
                        onClick={handleImageRemove}
                        className="px-2.5 py-1 text-xs bg-red-500 text-white border border-red-500 rounded hover:bg-red-600 hover:border-red-600 transition-all duration-150"
                      >
                        삭제
                      </button>
                    )}
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  className="hidden"
                />
              </div>
              <div className="flex-1 w-full space-y-3 sm:space-y-4">
                {/* ID (수정 불가) */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    ID
                  </label>
                  <div className="px-4 py-2 bg-gray-50 border-2 border-gray-200 rounded-lg text-slate-900">
                    {user.id}
                  </div>
                </div>

                {/* 이름 */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    이름
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-primary transition-all"
                      placeholder="이름을 입력하세요"
                    />
                  ) : (
                    <div className="px-4 py-2 bg-gray-50 border-2 border-gray-200 rounded-lg text-slate-900">
                      {user.name ? user.name : "미설정"}
                    </div>
                  )}
                </div>

                {/* 이메일 */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    이메일
                  </label>
                  {isEditing ? (
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-primary transition-all"
                      placeholder="이메일을 입력하세요"
                    />
                  ) : (
                    <div className="px-4 py-2 bg-gray-50 border-2 border-gray-200 rounded-lg text-slate-900">
                      {user.email ? user.email : "미설정"}
                    </div>
                  )}
                </div>

                {/* 역할 (수정 불가) */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    역할
                  </label>
                  <div className="px-4 py-2 bg-gray-50 border-2 border-gray-200 rounded-lg">
                    <span className={`px-3 py-1 rounded-md text-xs font-medium inline-block ${
                      user.role === "instructor" 
                        ? "bg-purple-100 text-purple-700" 
                        : "bg-blue-100 text-blue-700"
                    }`}>
                      {user.role === "instructor" ? "강사" : "학생"}
                    </span>
                  </div>
                </div>

                {/* 전문분야 (강사만) */}
                {user.role === "instructor" && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      전문분야
                    </label>
                    {isEditing ? (
                      <select
                        value={formData.specialization}
                        onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
                        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-primary transition-all"
                      >
                        <option value="">선택하세요</option>
                        <option value="국어">국어</option>
                        <option value="수학">수학</option>
                        <option value="영어">영어</option>
                        <option value="사회">사회</option>
                        <option value="한국사">한국사</option>
                        <option value="물리">물리</option>
                        <option value="화학">화학</option>
                        <option value="생명과학">생명과학</option>
                        <option value="지구과학">지구과학</option>
                        <option value="기타">기타</option>
                      </select>
                    ) : (
                      <div className="px-4 py-2 bg-gray-50 border-2 border-gray-200 rounded-lg text-slate-900">
                        {user.specialization ? user.specialization : "미설정"}
                      </div>
                    )}
                  </div>
                )}

                {/* 자기소개 (강사만) */}
                {user.role === "instructor" && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      자기소개
                    </label>
                    {isEditing ? (
                      <textarea
                        value={formData.bio}
                        onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                        rows={4}
                        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-primary transition-all resize-none"
                        placeholder="자기소개를 입력하세요"
                      />
                    ) : (
                      <div className="px-4 py-2 bg-gray-50 border-2 border-gray-200 rounded-lg text-slate-900 min-h-[80px] whitespace-pre-wrap">
                        {user.bio ? user.bio : "미설정"}
                      </div>
                    )}
                  </div>
                )}

                {/* 학생은 수정 불가 안내 */}
                {user.role === "student" && (
                  <div className="p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-700">
                      학생 계정은 프로필 수정 기능이 제공되지 않습니다.
                    </p>
                  </div>
                )}

                {/* 에러/성공 메시지 */}
                {error && (
                  <div className="p-4 bg-red-50 border-2 border-red-200 rounded-lg">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                )}
                {success && (
                  <div className="p-4 bg-green-50 border-2 border-green-200 rounded-lg">
                    <p className="text-sm text-green-700">{success}</p>
                  </div>
                )}

                {/* 수정 모드 버튼 */}
                {isEditing && (
                  <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 pt-3 sm:pt-4">
                    <button
                      onClick={handleSave}
                      disabled={isSaving}
                      className="flex items-center justify-center gap-2 px-3 sm:px-4 py-2 bg-primary text-white rounded-lg hover:bg-secondary transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                    >
                      <Save className="h-3 w-3 sm:h-4 sm:w-4" />
                      <span>{isSaving ? "저장 중..." : "저장"}</span>
                    </button>
                    <button
                      onClick={handleCancel}
                      disabled={isSaving}
                      className="flex items-center justify-center gap-2 px-3 sm:px-4 py-2 border-2 border-gray-300 rounded-lg hover:bg-gray-100 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                    >
                      <X className="h-3 w-3 sm:h-4 sm:w-4" />
                      <span>취소</span>
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* 하단 버튼 */}
            <div className="pt-4 sm:pt-6 border-t border-gray-200 flex flex-col sm:flex-row gap-2 sm:gap-3 justify-end">
              <Link
                href={user.role === "instructor" ? "/instructor/courses" : "/student/courses"}
                className="flex items-center justify-center gap-2 px-3 sm:px-4 py-2 border-2 border-gray-300 rounded-lg hover:bg-primary hover:text-white hover:border-primary transition-all duration-150 text-sm sm:text-base"
              >
                <span>강의 관리</span>
              </Link>
              <button
                onClick={handleLogout}
                className="flex items-center justify-center gap-2 px-3 sm:px-4 py-2 border-2 border-gray-300 rounded-lg hover:bg-red-500 hover:text-white hover:border-red-500 transition-all duration-150 text-sm sm:text-base"
              >
                <LogOut className="h-3 w-3 sm:h-4 sm:w-4" />
                <span>로그아웃</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
