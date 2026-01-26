"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { login, type LoginRequest, getInstructorProfile } from "@/lib/authApi";
import { saveToken, saveUser } from "@/lib/auth";

type LoginModalProps = {
  onClose: () => void;
  onSuccess: (data: { user_id: string; role: string }) => void;
};

export default function LoginModal({ onClose, onSuccess }: LoginModalProps) {
  const [formData, setFormData] = useState<LoginRequest>({
    user_id: "",
    password: "",
    role: "instructor",
  });
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await login(formData);
      
      // 토큰 저장
      saveToken(response.access_token);
      
      // 사용자 정보 저장 (기본 정보)
      let userInfo: { id: string; role: string; name?: string; email?: string } = {
        id: response.user_id,
        role: response.role,
      };

      // 강사인 경우 프로필 정보 가져오기
      if (response.role === "instructor") {
        try {
          const profile = await getInstructorProfile(response.access_token);
          userInfo.name = profile.name;
          userInfo.email = profile.email;
        } catch (profileErr) {
          console.error("프로필 정보 로드 실패:", profileErr);
          // 프로필 로드 실패해도 로그인은 진행
        }
      }

      saveUser(userInfo);

      onSuccess({
        user_id: response.user_id,
        role: response.role,
      });
    } catch (err: any) {
      setError(err.message || "로그인에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-[80%] sm:max-w-md rounded-2xl bg-white p-4 sm:p-6 shadow-xl max-h-[90vh] overflow-y-auto">
        {/* 닫기 버튼 */}
        <button
          onClick={onClose}
          className="absolute right-3 sm:right-4 top-3 sm:top-4 text-slate-400 hover:text-slate-600 z-10"
        >
          <X className="h-4 w-4 sm:h-5 sm:w-5" />
        </button>

        {/* 제목 */}
        <h2 className="mb-4 sm:mb-6 text-xl sm:text-2xl font-bold text-slate-900">로그인</h2>

        {/* 폼 */}
        <form onSubmit={handleSubmit} className="space-y-3 sm:space-y-4">
          {/* 역할 선택 */}
          <div>
            <label htmlFor="role" className="mb-1.5 sm:mb-2 block text-xs sm:text-sm font-medium text-slate-700">
              역할
            </label>
            <select
              id="role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              className="w-full rounded-lg border border-slate-300 px-3 sm:px-4 py-2 text-xs sm:text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="instructor">강사</option>
              <option value="student">학생</option>
            </select>
          </div>

          {/* 사용자 ID */}
          <div>
            <label htmlFor="user_id" className="mb-1.5 sm:mb-2 block text-xs sm:text-sm font-medium text-slate-700">
              사용자 ID
            </label>
            <input
              type="text"
              id="user_id"
              name="user_id"
              value={formData.user_id}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-slate-300 px-3 sm:px-4 py-2 text-xs sm:text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="사용자 ID를 입력하세요"
            />
          </div>

          {/* 비밀번호 */}
          <div>
            <label htmlFor="password" className="mb-1.5 sm:mb-2 block text-xs sm:text-sm font-medium text-slate-700">
              비밀번호
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-slate-300 px-3 sm:px-4 py-2 text-xs sm:text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="비밀번호를 입력하세요"
            />
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="rounded-lg bg-red-50 p-2.5 sm:p-3 text-xs sm:text-sm text-red-600">
              {error}
            </div>
          )}

          {/* 제출 버튼 */}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 sm:py-2 text-xs sm:text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "로그인 중..." : "로그인"}
          </button>
        </form>
      </div>
    </div>
  );
}
