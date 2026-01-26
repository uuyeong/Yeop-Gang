/**
 * 인증 관련 API 함수
 * 별도 파일로 분리하여 번들링 문제 해결
 */

import { apiFetch, apiPost, apiPatch, apiGet, getHttpErrorMessage, handleApiError } from "./api";

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
  console.log("회원가입 요청 데이터:", { ...data, password: "***" });

  try {
    const result = await apiPost<TokenResponse>("/api/auth/register/instructor", data);
    console.log("회원가입 성공:", result);
    return result;
  } catch (error) {
    console.error("회원가입 예외:", error);
    throw error; // apiPost가 이미 handleApiError를 처리함
  }
}

/**
 * 로그인
 */
export async function login(data: LoginRequest): Promise<TokenResponse> {
  try {
    return await apiPost<TokenResponse>("/api/auth/login", data);
  } catch (error) {
    throw error; // apiPost가 이미 handleApiError를 처리함
  }
}

/**
 * 강사 프로필 정보 조회
 */
export async function getInstructorProfile(
  token: string
): Promise<InstructorProfileResponse> {
  try {
    console.log("[authApi] 프로필 조회 요청");
    const result = await apiGet<InstructorProfileResponse>("/api/instructor/profile", {
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    });
    console.log("[authApi] 프로필 조회 응답:", {
      ...result,
      profile_image_url: result.profile_image_url ? `${result.profile_image_url.substring(0, 50)}...` : null,
    });
    return result;
  } catch (error) {
    console.error("[authApi] 프로필 조회 예외:", error);
    throw error; // apiGet이 이미 handleApiError를 처리함
  }
}

/**
 * 강사 프로필(개인정보) 수정
 */
export async function updateInstructorProfile(
  token: string,
  data: UpdateInstructorRequest
): Promise<{ message: string; name?: string; email?: string; profile_image_url?: string | null; [k: string]: unknown }> {
  console.log("[authApi] 프로필 업데이트 요청:", {
    ...data,
    profile_image_url: data.profile_image_url ? `${data.profile_image_url.substring(0, 50)}...` : null,
  });
  try {
    const result = await apiPatch<{ message: string; name?: string; email?: string; profile_image_url?: string | null; [k: string]: unknown }>("/api/instructor/profile", data, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    console.log("[authApi] 프로필 업데이트 응답:", {
      ...result,
      profile_image_url: result.profile_image_url ? `${result.profile_image_url.substring(0, 50)}...` : null,
    });
    return result;
  } catch (error) {
    console.error("[authApi] 프로필 업데이트 예외:", error);
    throw error; // apiPatch가 이미 handleApiError를 처리함
  }
}
