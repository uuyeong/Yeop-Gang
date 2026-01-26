/**
 * API 공통 유틸리티
 * - API 기본 URL 관리
 * - 공통 fetch 함수
 * - 에러 처리
 */

// API 기본 URL 결정
// Render 환경: Next.js API Routes 프록시 사용 (상대 경로)
// 로컬 개발: 절대 URL 사용
const getApiBaseUrl = () => {
  // 환경 변수가 설정되어 있으면 사용
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // 브라우저 환경에서는 상대 경로 사용 (Next.js API Routes가 프록시)
  if (typeof window !== 'undefined') {
    return '';
  }
  
  // 서버 사이드에서는 절대 URL 사용
  return "http://localhost:8000";
};

export const API_BASE_URL = getApiBaseUrl();

export type ApiError = {
  message: string;
  status?: number;
  code?: string;
};

/**
 * 공통 API 에러 처리
 */
export function handleApiError(error: unknown): ApiError {
  // 네트워크 오류
  if (error instanceof TypeError && error.message.includes("fetch")) {
    console.error('[handleApiError] 네트워크 오류 감지:', {
      message: error.message,
      name: error.name,
      stack: error.stack,
    });
    return {
      message:
        "네트워크 연결을 확인할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.",
      code: "NETWORK_ERROR",
    };
  }
  
  // Error 객체이고 메시지에 특정 키워드가 포함된 경우
  if (error instanceof Error) {
    console.error('[handleApiError] Error 객체:', {
      message: error.message,
      name: error.name,
      stack: error.stack,
    });
    
    // 프록시 실패 메시지인 경우
    if (error.message.includes('백엔드 서버에 연결할 수 없습니다') || 
        error.message.includes('프록시 요청 실패')) {
      return {
        message: error.message,
        code: "PROXY_ERROR",
      };
    }
  }

  // 일반 Error 객체
  if (error instanceof Error) {
    return {
      message: error.message,
    };
  }

  // 알 수 없는 오류
  return {
    message: "알 수 없는 오류가 발생했습니다.",
    code: "UNKNOWN_ERROR",
  };
}

/**
 * HTTP 상태 코드에 따른 에러 메시지 생성
 */
export function getHttpErrorMessage(status: number): string {
  switch (status) {
    case 400:
      return "잘못된 요청입니다. 입력값을 확인해주세요.";
    case 401:
      return "인증이 필요합니다.";
    case 403:
      return "접근 권한이 없습니다.";
    case 404:
      return "요청한 리소스를 찾을 수 없습니다.";
    case 413:
      return "파일 크기가 너무 큽니다.";
    case 429:
      return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.";
    case 500:
      return "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
    case 503:
      return "서버가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.";
    default:
      return `서버 오류 (${status})`;
  }
}

/**
 * 공통 fetch 래퍼 함수
 */
export async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  // URL 생성
  let url: string;
  if (endpoint.startsWith("http")) {
    // 절대 URL이면 그대로 사용
    url = endpoint;
  } else {
    // 상대 경로인 경우
    if (API_BASE_URL) {
      // API_BASE_URL이 있으면 붙여서 사용
      url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
    } else {
      // API_BASE_URL이 비어있으면 상대 경로 그대로 사용 (Next.js API Routes가 프록시)
      // 브라우저 환경에서는 /api/...로 시작하는 경로가 Next.js API Routes로 자동 라우팅됨
      url = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
    }
  }

  try {
    // 인증 토큰이 있으면 Authorization 헤더 추가
    const token = typeof window !== 'undefined' 
      ? (localStorage.getItem("token") || localStorage.getItem("instructor_token") || "")
      : "";
    
    // options?.headers를 Record<string, string>로 변환
    const existingHeaders: Record<string, string> = options?.headers 
      ? (options.headers instanceof Headers
          ? Object.fromEntries(options.headers.entries())
          : Array.isArray(options.headers)
          ? Object.fromEntries(options.headers)
          : options.headers as Record<string, string>)
      : {};
    
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...existingHeaders,
    };
    
    // Authorization 헤더가 없고 토큰이 있으면 추가
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    console.log(`[apiFetch] 요청 URL: ${url}`);
    console.log(`[apiFetch] 메서드: ${options?.method || 'GET'}`);
    console.log(`[apiFetch] API_BASE_URL: ${API_BASE_URL || '(빈 문자열 - 상대 경로 사용)'}`);
    console.log(`[apiFetch] 브라우저 환경: ${typeof window !== 'undefined'}`);
    
    let response: Response;
    try {
      response = await fetch(url, {
        ...options,
        headers,
      });
    } catch (fetchError) {
      console.error(`[apiFetch] fetch 실패:`, fetchError);
      // 네트워크 오류인 경우 더 자세한 정보 제공
      if (fetchError instanceof TypeError) {
        console.error(`[apiFetch] 네트워크 오류 상세:`, {
          message: fetchError.message,
          url: url,
          isRelative: !url.startsWith('http'),
        });
      }
      throw fetchError;
    }

    console.log(`[apiFetch] 응답 상태: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      // 503 에러인 경우 프록시 실패로 간주
      if (response.status === 503) {
        const errorData = await response.json().catch(() => ({}));
        console.error('[apiFetch] 프록시 실패:', errorData);
        throw new Error(errorData.message || '백엔드 서버에 연결할 수 없습니다.');
      }
      const errorMessage = getHttpErrorMessage(response.status);
      throw new Error(errorMessage);
    }

    // 빈 응답 처리
    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      return {} as T;
    }

    return await response.json();
  } catch (error) {
    throw handleApiError(error);
  }
}

/**
 * POST 요청 헬퍼
 */
export async function apiPost<T>(
  endpoint: string,
  data?: unknown,
  options?: RequestInit
): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: "POST",
    body: data ? JSON.stringify(data) : undefined,
    ...options,
  });
}

/**
 * GET 요청 헬퍼
 */
export async function apiGet<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: "GET",
    ...options,
  });
}

/**
 * PATCH 요청 헬퍼
 */
export async function apiPatch<T>(
  endpoint: string,
  data?: unknown,
  options?: RequestInit
): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: "PATCH",
    body: data ? JSON.stringify(data) : undefined,
    ...options,
  });
}

/**
 * DELETE 요청 헬퍼
 */
export async function apiDelete<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: "DELETE",
    ...options,
  });
}

/**
 * 파일 업로드용 POST 요청
 */
export async function apiUpload<T>(
  endpoint: string,
  formData: FormData,
  options?: RequestInit
): Promise<T> {
  // URL 생성 (apiFetch와 동일한 로직)
  let url: string;
  if (endpoint.startsWith("http")) {
    url = endpoint;
  } else {
    if (API_BASE_URL) {
      url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
    } else {
      url = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
    }
  }

  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      ...options,
    });

    if (!response.ok) {
      const errorMessage = getHttpErrorMessage(response.status);
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    throw handleApiError(error);
  }
}

// 인증 API는 client/lib/authApi.ts에서 제공됩니다.
