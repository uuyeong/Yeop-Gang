/**
 * Next.js API Routes 프록시 (AI 엔드포인트)
 * Render 환경에서 클라이언트 사이드 요청을 백엔드로 프록시
 */
import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path);
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path);
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path);
}

async function proxyRequest(request: NextRequest, pathSegments: string[]) {
  const maxRetries = 3;
  let lastError: Error | null = null;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const path = pathSegments.join('/');
      const url = new URL(request.url);
      const searchParams = url.searchParams.toString();
      const queryString = searchParams ? `?${searchParams}` : '';
      
      const backendUrl = `${BACKEND_URL}/ai/${path}${queryString}`;
      
      // 요청 본문 가져오기
      let body: BodyInit | undefined;
      const contentType = request.headers.get('content-type');
      
      if (contentType?.includes('multipart/form-data')) {
        body = await request.formData();
      } else if (contentType?.includes('application/json')) {
        body = await request.text();
      } else {
        const text = await request.text();
        body = text || undefined;
      }
      
      // 헤더 복사 (호스트 헤더 제외)
      const headers = new Headers();
      request.headers.forEach((value, key) => {
        const lowerKey = key.toLowerCase();
        if (lowerKey !== 'host' && lowerKey !== 'connection') {
          headers.set(key, value);
        }
      });
      
      // 백엔드로 요청 전달 (타임아웃 설정)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30초 타임아웃
      
      try {
        const response = await fetch(backendUrl, {
          method: request.method,
          headers,
          body,
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        
        // 응답 본문 가져오기
        const responseBody = await response.text();
        
        // 응답 헤더 복사
        const responseHeaders = new Headers();
        response.headers.forEach((value, key) => {
          // CORS 헤더는 Next.js가 처리하므로 제외
          const lowerKey = key.toLowerCase();
          if (lowerKey !== 'access-control-allow-origin' && 
              lowerKey !== 'access-control-allow-methods' &&
              lowerKey !== 'access-control-allow-headers') {
            responseHeaders.set(key, value);
          }
        });
        
        return new NextResponse(responseBody, {
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders,
        });
      } catch (fetchError) {
        clearTimeout(timeoutId);
        throw fetchError;
      }
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      // ECONNREFUSED 오류인 경우 재시도
      if (error instanceof Error && 
          (error.message.includes('ECONNREFUSED') || 
           error.message.includes('fetch failed'))) {
        if (attempt < maxRetries) {
          const waitTime = attempt * 1000; // 1초, 2초, 3초 대기
          console.warn(`[AI Proxy] 백엔드 연결 실패 (시도 ${attempt}/${maxRetries}), ${waitTime}ms 후 재시도...`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
          continue;
        }
      }
      
      // 재시도 불가능한 오류이거나 최대 재시도 횟수 초과
      console.error('[AI Proxy] Error:', error);
      return NextResponse.json(
        { 
          error: '프록시 요청 실패', 
          message: lastError.message,
          details: process.env.NODE_ENV === 'development' ? String(error) : undefined
        },
        { status: 503 } // Service Unavailable
      );
    }
  }
  
  // 모든 재시도 실패
  return NextResponse.json(
    { 
      error: '백엔드 서버에 연결할 수 없습니다', 
      message: lastError?.message || 'Unknown error'
    },
    { status: 503 }
  );
}
