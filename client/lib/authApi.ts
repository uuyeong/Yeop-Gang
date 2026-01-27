/**
 * 인증 관련 API 함수
 * 별도 파일로 분리하여 번들링 문제 해결
 */

import { getApiBaseUrlValue, getHttpErrorMessage, handleApiError } from "./api";

export type RegisterInstructorRequest = {
  id: string;
  name: string;
  email: string;
  password: string;
  bio?: string;
  specialization: string; // 필수 필드
  initial_courses?: Array<{ course_id: string; title: string }>;
};

export type LoginRequest = {
  user_id: string;
  password: string;
  role: "instructor" | "student";
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  role: string;
  expires_in: number;
};

export type InstructorProfileResponse = {
  id: string;
  name: string;
  email: string;
  profile_image_url?: string | null;
  bio?: string | null;
  phone?: string | null;
  specialization?: string | null;
  created_at: string;
  updated_at: string;
  course_count: number;
};

/** 강사 프로필(개인정보) 수정 요청 - 보낸 필드만 반영 */
export type UpdateInstructorRequest = {
  name?: string | null;
  email?: string | null;
  profile_image_url?: string | null;
  bio?: string | null;
  phone?: string | null;
  specialization?: string | null;
};

/**
 * 강사 회원가입
 */
export async function registerInstructor(
  data: RegisterInstructorRequest
): Promise<TokenResponse> {
  const API_BASE_URL = getApiBaseUrlValue();
  const url = `${API_BASE_URL}/api/auth/register/instructor`;
  console.log("회원가입 요청 URL:", url);
  console.log("회원가입 요청 데이터:", { ...data, password: "***" });

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    console.log("회원가입 응답 상태:", response.status, response.statusText);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("회원가입 에러 응답:", errorData);
      const errorMessage = errorData.detail || errorData.message || getHttpErrorMessage(response.status);
      throw new Error(errorMessage);
    }

    const result = await response.json();
    console.log("회원가입 성공:", result);
    return result;
  } catch (error) {
    console.error("회원가입 예외:", error);
    throw handleApiError(error);
  }
}

/**
 * 로그인
 */
export async function login(data: LoginRequest): Promise<TokenResponse> {
  try {
    const API_BASE_URL = getApiBaseUrlValue();
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || getHttpErrorMessage(response.status));
    }

    return await response.json();
  } catch (error) {
    throw handleApiError(error);
  }
}

/**
 * 강사 프로필 정보 조회
 */
export async function getInstructorProfile(
  token: string
): Promise<InstructorProfileResponse> {
  const API_BASE_URL = getApiBaseUrlValue();
  const url = `${API_BASE_URL}/api/instructor/profile`;
  
  try {
    console.log("[authApi] 프로필 조회 요청:", url);
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.detail || errorData.message || getHttpErrorMessage(response.status);
      throw new Error(errorMessage);
    }

    const result = await response.json();
    console.log("[authApi] 프로필 조회 응답:", {
      ...result,
      profile_image_url: result.profile_image_url ? `${result.profile_image_url.substring(0, 50)}...` : null,
    });
    return result;
  } catch (error) {
    console.error("[authApi] 프로필 조회 예외:", error);
    throw handleApiError(error);
  }
}

/**
 * 강사 프로필(개인정보) 수정
 */
export async function updateInstructorProfile(
  token: string,
  data: UpdateInstructorRequest
): Promise<{ message: string; name?: string; email?: string; profile_image_url?: string | null; [k: string]: unknown }> {
  const API_BASE_URL = getApiBaseUrlValue();
  const url = `${API_BASE_URL}/api/instructor/profile`;
  console.log("[authApi] 프로필 업데이트 요청:", {
    ...data,
    profile_image_url: data.profile_image_url ? `${data.profile_image_url.substring(0, 50)}...` : null,
  });
  const response = await fetch(url, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const msg = errorData.detail || errorData.message || getHttpErrorMessage(response.status);
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  const result = await response.json();
  console.log("[authApi] 프로필 업데이트 응답:", {
    ...result,
    profile_image_url: result.profile_image_url ? `${result.profile_image_url.substring(0, 50)}...` : null,
  });
  return result;
}
