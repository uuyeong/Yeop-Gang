"use client";

import { useState } from "react";
import { X } from "lucide-react";
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
    profile_image_url: "",
    bio: "",
    phone: "",
    specialization: "",
  });
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

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
      // 빈 필드는 undefined로 변환
      const payload: RegisterInstructorRequest = {
        id: formData.id,
        name: formData.name,
        email: formData.email,
        password: formData.password,
        profile_image_url: formData.profile_image_url || undefined,
        bio: formData.bio || undefined,
        phone: formData.phone || undefined,
        specialization: formData.specialization || undefined,
      };

      console.log("회원가입 요청:", { ...payload, password: "***" });

      const response = await registerInstructor(payload);

      console.log("회원가입 성공:", response);

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
      console.error("회원가입 에러:", err);
      // 더 자세한 에러 메시지 표시
      let errorMessage = "회원가입에 실패했습니다.";
      if (err.message) {
        errorMessage = err.message;
      } else if (err instanceof Error) {
        errorMessage = err.toString();
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

          {/* 전화번호 */}
          <div>
            <label htmlFor="phone" className="mb-2 block text-sm font-medium text-slate-700">
              전화번호
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="010-1234-5678"
            />
          </div>

          {/* 전문 분야 */}
          <div>
            <label htmlFor="specialization" className="mb-2 block text-sm font-medium text-slate-700">
              전문 분야
            </label>
            <input
              type="text"
              id="specialization"
              name="specialization"
              value={formData.specialization}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="예: 수학, 영어, 물리"
            />
          </div>

          {/* 프로필 이미지 URL */}
          <div>
            <label htmlFor="profile_image_url" className="mb-2 block text-sm font-medium text-slate-700">
              프로필 이미지 URL
            </label>
            <input
              type="url"
              id="profile_image_url"
              name="profile_image_url"
              value={formData.profile_image_url}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="https://example.com/profile.jpg"
            />
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
