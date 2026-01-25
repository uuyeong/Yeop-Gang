"use client";

import { useState, useRef } from "react";
import { X, Upload, User, XCircle } from "lucide-react";
import { registerInstructor, type RegisterInstructorRequest } from "@/lib/authApi";
import { saveToken, saveUser } from "@/lib/auth";

type RegisterModalProps = {
  onClose: () => void;
  onSuccess: (data: { user_id: string; role: string }) => void;
};

export default function RegisterModal({ onClose, onSuccess }: RegisterModalProps) {
  const [formData, setFormData] = useState<RegisterInstructorRequest>({
    id: "",
    name: "",
    email: "",
    password: "",
    bio: "",
    specialization: "",
  });
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [profileImage, setProfileImage] = useState<File | null>(null);
  const [profileImagePreview, setProfileImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // 비밀번호 최소 길이 검증
    if (formData.password.length < 8) {
      setError("비밀번호는 최소 8자 이상이어야 합니다.");
      setLoading(false);
      return;
    }

    try {
      // 전문분야 필수 검증
      if (!formData.specialization || !formData.specialization.trim()) {
        setError("전문분야는 필수 항목입니다.");
        setLoading(false);
        return;
      }

      // 빈 필드는 undefined로 변환 (빈 문자열, 공백만 있는 경우 포함)
      const payload: RegisterInstructorRequest = {
        id: formData.id.trim(),
        name: formData.name.trim(),
        email: formData.email.trim(),
        password: formData.password,
        bio: formData.bio?.trim() || undefined,
        specialization: formData.specialization.trim(),
      };

      console.log("[RegisterModal] 회원가입 요청:", { ...payload, password: "***" });

      const response = await registerInstructor(payload);

      console.log("[RegisterModal] 회원가입 성공:", response);

      // 토큰 저장
      saveToken(response.access_token);

      // 사용자 정보 저장
      saveUser({
        id: response.user_id,
        role: response.role,
        name: formData.name,
        email: formData.email,
      });

      onSuccess({
        user_id: response.user_id,
        role: response.role,
      });
    } catch (err: any) {
      console.error("[RegisterModal] 회원가입 에러:", err);
      console.error("[RegisterModal] 에러 상세:", {
        message: err.message,
        stack: err.stack,
        name: err.name,
        response: err.response,
      });
      
      // 더 자세한 에러 메시지 표시
      let errorMessage = "회원가입에 실패했습니다.";
      if (err.message) {
        errorMessage = err.message;
      } else if (err instanceof Error) {
        errorMessage = err.toString();
      } else if (typeof err === "string") {
        errorMessage = err;
      }
      
      // 백엔드 validation 에러 메시지 파싱
      if (err.message && typeof err.message === "string") {
        // FastAPI validation 에러 형식: "detail": [{"loc": [...], "msg": "...", "type": "..."}]
        try {
          const errorObj = JSON.parse(err.message);
          if (errorObj.detail && Array.isArray(errorObj.detail)) {
            const firstError = errorObj.detail[0];
            if (firstError.msg) {
              errorMessage = `${firstError.loc?.join(".") || "입력값"}: ${firstError.msg}`;
            }
          } else if (errorObj.detail && typeof errorObj.detail === "string") {
            errorMessage = errorObj.detail;
          }
        } catch {
          // JSON 파싱 실패 시 원본 메시지 사용
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // 이미지 파일만 허용
      if (!file.type.startsWith("image/")) {
        setError("이미지 파일만 업로드 가능합니다.");
        return;
      }

      // 파일 크기 제한 (5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError("이미지 크기는 5MB 이하여야 합니다.");
        return;
      }

      setProfileImage(file);
      setError("");

      // 미리보기 생성
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfileImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleImageRemove = () => {
    setProfileImage(null);
    setProfileImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleImageClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
        {/* 닫기 버튼 */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-slate-600"
        >
          <X className="h-5 w-5" />
        </button>

        {/* 제목 */}
        <h2 className="mb-6 text-2xl font-bold text-slate-900">강사 회원가입</h2>

        {/* 폼 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 프로필 이미지 업로드 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">
              프로필 이미지
            </label>
            <div className="flex flex-col items-center gap-4">
              {/* 프로필 이미지 미리보기 */}
              <div
                onClick={handleImageClick}
                className="relative cursor-pointer group"
              >
                {profileImagePreview ? (
                  <div className="relative">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={profileImagePreview}
                      alt="프로필 미리보기"
                      className="h-24 w-24 rounded-full object-cover border-2 border-slate-300 group-hover:border-blue-500 transition-colors"
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
              
              {/* 업로드 버튼 */}
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

          {/* 강사 ID */}
          <div>
            <label htmlFor="id" className="mb-2 block text-sm font-medium text-slate-700">
              강사 ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="id"
              name="id"
              value={formData.id}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="강사 ID를 입력하세요"
            />
          </div>

          {/* 이름 */}
          <div>
            <label htmlFor="name" className="mb-2 block text-sm font-medium text-slate-700">
              이름 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="이름을 입력하세요"
            />
          </div>

          {/* 이메일 */}
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-slate-700">
              이메일 <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="이메일을 입력하세요"
            />
          </div>

          {/* 비밀번호 */}
          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-slate-700">
              비밀번호 <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={8}
              className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="비밀번호 (최소 8자)"
            />
            <p className="mt-1 text-xs text-slate-500">비밀번호는 최소 8자 이상이어야 합니다.</p>
          </div>

          {/* 전문 분야 */}
          <div>
            <label htmlFor="specialization" className="mb-2 block text-sm font-medium text-slate-700">
              전문 분야 <span className="text-red-500">*</span>
            </label>
            <select
              id="specialization"
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
            <p className="mt-1 text-xs text-slate-500"></p>
          </div>

          {/* 자기소개 */}
          <div>
            <label htmlFor="bio" className="mb-2 block text-sm font-medium text-slate-700">
              자기소개
            </label>
            <textarea
              id="bio"
              name="bio"
              value={formData.bio}
              onChange={handleChange}
              rows={3}
              className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="자기소개를 입력하세요"
            />
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          {/* 제출 버튼 */}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "회원가입 중..." : "회원가입"}
          </button>
        </form>
      </div>
    </div>
  );
}
