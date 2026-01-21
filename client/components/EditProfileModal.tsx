"use client";

import { useState, useEffect, useRef } from "react";
import { X, Upload, User, XCircle } from "lucide-react";
import {
  getInstructorProfile,
  updateInstructorProfile,
  type UpdateInstructorRequest,
  type InstructorProfileResponse,
} from "@/lib/authApi";

type EditProfileModalProps = {
  isOpen: boolean;
  onClose: () => void;
  token: string;
  onSuccess?: (data: InstructorProfileResponse & { name?: string; email?: string }) => void;
};

export default function EditProfileModal({
  isOpen,
  onClose,
  token,
  onSuccess,
}: EditProfileModalProps) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    bio: "",
    specialization: "",
  });
  const [profileImage, setProfileImage] = useState<File | null>(null);
  const [profileImagePreview, setProfileImagePreview] = useState<string | null>(null);
  const [existingImageUrl, setExistingImageUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen && token) {
      setError("");
      setFetching(true);
      getInstructorProfile(token)
        .then((p) => {
          console.log("[EditProfileModal] 프로필 로드:", p);
          setFormData({
            name: p.name ?? "",
            email: p.email ?? "",
            password: "", // 비밀번호는 항상 빈 값으로 시작 (변경 시에만 입력)
            bio: p.bio ?? "",
            specialization: p.specialization ?? "",
          });
          // 기존 프로필 이미지 URL 저장
          if (p.profile_image_url && p.profile_image_url.trim()) {
            console.log("[EditProfileModal] 기존 이미지 URL:", p.profile_image_url.substring(0, 50) + "...");
            setExistingImageUrl(p.profile_image_url);
            setProfileImagePreview(p.profile_image_url);
          } else {
            console.log("[EditProfileModal] 이미지 없음");
            setExistingImageUrl(null);
            setProfileImagePreview(null);
          }
          setProfileImage(null);
        })
        .catch((e) => {
          console.error("[EditProfileModal] 프로필 로드 실패:", e);
          setError(e?.message || "프로필을 불러올 수 없습니다.");
        })
        .finally(() => setFetching(false));
    } else if (!isOpen) {
      // 모달이 닫힐 때 상태 초기화
      setFormData({
        name: "",
        email: "",
        password: "",
        bio: "",
        specialization: "",
      });
      setProfileImage(null);
      setProfileImagePreview(null);
      setExistingImageUrl(null);
      setError("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }, [isOpen, token]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
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
        console.error("[EditProfileModal] 이미지 읽기 실패");
        setError("이미지를 읽을 수 없습니다.");
      };
      reader.onloadend = () => {
        const result = reader.result as string;
        console.log("[EditProfileModal] 이미지 미리보기 생성:", result.substring(0, 50) + "...");
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
    fileInputRef.current?.click();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
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

      const payload: UpdateInstructorRequest = {
        name: formData.name,
        email: formData.email,
        profile_image_url: profileImageUrl,
        bio: formData.bio || undefined,
        specialization: formData.specialization || undefined,
      };
      console.log("[EditProfileModal] 업데이트 요청:", { ...payload, profile_image_url: payload.profile_image_url?.substring(0, 50) + "..." });
      const res = await updateInstructorProfile(token, payload);
      console.log("[EditProfileModal] 업데이트 성공:", res);
      // profile_image_url을 명시적으로 전달
      onSuccess?.({
        ...res,
        name: res.name ?? formData.name,
        email: res.email ?? formData.email,
        profile_image_url: res.profile_image_url ?? profileImageUrl ?? undefined,
      });
      onClose();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "수정에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-slate-600"
          type="button"
        >
          <X className="h-5 w-5" />
        </button>

        <h2 className="mb-6 text-2xl font-bold text-slate-900">회원정보 수정</h2>

        {fetching ? (
          <p className="py-8 text-center text-slate-500">불러오는 중...</p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 프로필 이미지 업로드 */}
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                프로필 이미지
              </label>
              <div className="flex flex-col items-center gap-4">
                <div
                  onClick={handleImageClick}
                  className="relative cursor-pointer group"
                >
                  {profileImagePreview ? (
                    <div className="relative">
                      <img
                        src={profileImagePreview}
                        alt="프로필 미리보기"
                        className="h-24 w-24 rounded-full object-cover border-2 border-slate-300 group-hover:border-blue-500 transition-colors"
                        onError={(e) => {
                          console.error("[EditProfileModal] 이미지 로드 실패:", profileImagePreview.substring(0, 50));
                          setError("이미지를 표시할 수 없습니다.");
                          setProfileImagePreview(null);
                        }}
                        onLoad={() => {
                          console.log("[EditProfileModal] 이미지 로드 성공");
                        }}
                      />
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleImageRemove();
                        }}
                        className="absolute -top-1 -right-1 h-6 w-6 rounded-full bg-red-500 text-white flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg"
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="h-24 w-24 rounded-full bg-slate-100 border-2 border-dashed border-slate-300 flex flex-col items-center justify-center group-hover:border-blue-500 group-hover:bg-blue-50 transition-colors">
                      <User className="h-8 w-8 text-slate-400 group-hover:text-blue-500" />
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
                <button
                  type="button"
                  onClick={handleImageClick}
                  className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  <Upload className="h-4 w-4" />
                  <span>{profileImage ? "이미지 변경" : "이미지 선택"}</span>
                </button>
                {profileImage && (
                  <p className="text-xs text-slate-500">
                    선택된 파일: {profileImage.name} ({(profileImage.size / 1024).toFixed(1)}KB)
                  </p>
                )}
                <p className="text-xs text-slate-400 text-center">
                  권장 크기: 200x200px 이상<br />
                  지원 형식: JPG, PNG, GIF (최대 5MB)
                </p>
              </div>
            </div>
            <div>
              <label htmlFor="edit-name" className="mb-2 block text-sm font-medium text-slate-700">
                이름
              </label>
              <input
                type="text"
                id="edit-name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="이름"
              />
            </div>
            <div>
              <label htmlFor="edit-email" className="mb-2 block text-sm font-medium text-slate-700">
                이메일
              </label>
              <input
                type="email"
                id="edit-email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="이메일"
              />
            </div>
            <div>
              <label htmlFor="edit-specialization" className="mb-2 block text-sm font-medium text-slate-700">
                전문 분야 <span className="text-red-500">*</span>
              </label>
              <select
                id="edit-specialization"
                name="specialization"
                value={formData.specialization}
                onChange={handleChange}
                required
                className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">선택하세요</option>
                <option value="국어">국어</option>
                <option value="수학">수학</option>
                <option value="영어">영어</option>
                <option value="사회">사회</option>
                <option value="역사">역사</option>
                <option value="물리">물리</option>
                <option value="화학">화학</option>
                <option value="생명과학">생명과학</option>
                <option value="지구과학">지구과학</option>
                <option value="기타">기타</option>
              </select>
            </div>
            <div>
              <label htmlFor="edit-bio" className="mb-2 block text-sm font-medium text-slate-700">
                자기소개
              </label>
              <textarea
                id="edit-bio"
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                rows={3}
                className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="자기소개"
              />
            </div>
            {error && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "저장 중..." : "저장"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
