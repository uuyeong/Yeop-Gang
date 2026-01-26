/**
 * Next.js API Routes 프록시
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

export async function PUT(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path);
}

async function proxyRequest(request: NextRequest, pathSegments: string[]) {
  const maxRetries = 3;
  let lastError: Error | null = null;
  
  // 디버깅을 위한 로그 (항상 출력)
  const path = pathSegments.join('/');
  console.log(`[API Proxy] ========== 프록시 요청 시작 ==========`);
  console.log(`[API Proxy] 경로: /api/${path}`);
  console.log(`[API Proxy] 메서드: ${request.method}`);
  console.log(`[API Proxy] BACKEND_URL: ${BACKEND_URL}`);
  console.log(`[API Proxy] 요청 URL: ${request.url}`);
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const url = new URL(request.url);
      const searchParams = url.searchParams.toString();
      const queryString = searchParams ? `?${searchParams}` : '';
      
      const backendUrl = `${BACKEND_URL}/api/${path}${queryString}`;
      console.log(`[API Proxy] 시도 ${attempt}/${maxRetries}: ${backendUrl}`);
      
      // 요청 본문 가져오기 (GET/HEAD 요청은 body가 없어야 함)
      let body: BodyInit | undefined;
      const method = request.method.toUpperCase();
      const isGetOrHead = method === 'GET' || method === 'HEAD';
      
      if (!isGetOrHead) {
        const contentType = request.headers.get('content-type');
        
        if (contentType?.includes('multipart/form-data')) {
          body = await request.formData();
        } else if (contentType?.includes('application/json')) {
          body = await request.text();
        } else {
          const text = await request.text();
          body = text || undefined;
        }
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
        console.log(`[API Proxy] 백엔드로 요청 전송: ${request.method} ${backendUrl}`);
        const fetchOptions: RequestInit = {
          method: request.method,
          headers,
          signal: controller.signal,
        };
        
        // GET/HEAD 요청이 아닌 경우에만 body 추가
        if (!isGetOrHead && body !== undefined) {
          fetchOptions.body = body;
        }
        
        const response = await fetch(backendUrl, fetchOptions);
        
        clearTimeout(timeoutId);
        console.log(`[API Proxy] 백엔드 응답: ${response.status} ${response.statusText}`);
        
        // 비디오 스트리밍을 위한 처리
        const contentType = response.headers.get('content-type') || '';
        const isVideo = contentType.startsWith('video/') || 
                        contentType.startsWith('application/octet-stream') ||
                        pathSegments.some(seg => seg.includes('video'));
        
        if (isVideo) {
          // 비디오 파일은 스트리밍으로 전달
          const responseHeaders = new Headers();
          response.headers.forEach((value, key) => {
            const lowerKey = key.toLowerCase();
            if (lowerKey !== 'access-control-allow-origin' && 
                lowerKey !== 'access-control-allow-methods' &&
                lowerKey !== 'access-control-allow-headers') {
              responseHeaders.set(key, value);
            }
          });
          
          return new NextResponse(response.body, {
            status: response.status,
            statusText: response.statusText,
            headers: responseHeaders,
          });
        }
        
        // 일반 응답 본문 가져오기
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
        
        console.log(`[API Proxy] ✅ 프록시 성공: ${response.status} ${response.statusText}`);
        return new NextResponse(responseBody, {
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders,
        });
      } catch (fetchError) {
        clearTimeout(timeoutId);
        console.error(`[API Proxy] fetch 오류:`, fetchError);
        throw fetchError;
      }
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      const errorMessage = error instanceof Error ? error.message : String(error);
      const errorStack = error instanceof Error ? error.stack : undefined;
      
      console.error(`[API Proxy] 오류 발생 (시도 ${attempt}/${maxRetries}):`, {
        message: errorMessage,
        stack: errorStack,
        name: error instanceof Error ? error.name : 'Unknown',
      });
      
      // ECONNREFUSED 오류인 경우 재시도
      if (error instanceof Error && 
          (errorMessage.includes('ECONNREFUSED') || 
           errorMessage.includes('fetch failed') ||
           errorMessage.includes('ECONNREFUSED'))) {
        if (attempt < maxRetries) {
          const waitTime = attempt * 1000; // 1초, 2초, 3초 대기
          console.warn(`[API Proxy] 백엔드 연결 실패 (시도 ${attempt}/${maxRetries}), ${waitTime}ms 후 재시도...`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
          continue;
        }
      }
      
      // 재시도 불가능한 오류이거나 최대 재시도 횟수 초과
      console.error('[API Proxy] 최종 실패:', {
        error: errorMessage,
        backendUrl: `${BACKEND_URL}/api/${pathSegments.join('/')}`,
        attempts: attempt,
      });
      
      return NextResponse.json(
        { 
          error: '프록시 요청 실패', 
          message: lastError.message,
          backendUrl: `${BACKEND_URL}/api/${pathSegments.join('/')}`,
          details: process.env.NODE_ENV === 'development' ? {
            error: errorMessage,
            stack: errorStack,
          } : undefined
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
