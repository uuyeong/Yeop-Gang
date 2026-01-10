/**
 * 인증 토큰 관리 유틸리티
 */

const TOKEN_KEY = "yeopgang_access_token";
const USER_KEY = "yeopgang_user";

export type User = {
  id: string;
  role: string;
  name?: string;
  email?: string;
};

/**
 * 토큰 저장
 */
export function saveToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

/**
 * 토큰 가져오기
 */
export function getToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

/**
 * 토큰 삭제
 */
export function removeToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

/**
 * 사용자 정보 저장
 */
export function saveUser(user: User): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/**
 * 사용자 정보 가져오기
 */
export function getUser(): User | null {
  if (typeof window !== "undefined") {
    const userStr = localStorage.getItem(USER_KEY);
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
  }
  return null;
}

/**
 * 로그인 여부 확인
 */
export function isAuthenticated(): boolean {
  return getToken() !== null;
}

/**
 * 인증 헤더 생성
 */
export function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  if (token) {
    return {
      Authorization: `Bearer ${token}`,
    };
  }
  return {};
}
