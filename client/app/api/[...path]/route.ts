/**
 * Next.js API Routes 프록시
 * 통합 배포: 브라우저 요청을 같은 컨테이너 내 백엔드로 프록시
 */
import { NextRequest, NextResponse } from 'next/server';

// 통합 배포: 같은 컨테이너 내 백엔드 (localhost:8000)
const BACKEND_URL = 'http://localhost:8000';

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
  
  const path = pathSegments.join('/');
  console.log(`[API Proxy] ${request.method} /api/${path} → ${BACKEND_URL}/api/${path}`);
  
  // GET/HEAD 요청은 body를 포함하면 안 됨
  const method = request.method.toUpperCase();
  const canHaveBody = !['GET', 'HEAD'].includes(method);
  
  // 요청 본문 가져오기 (GET/HEAD가 아닌 경우에만, 루프 밖에서 한 번만 읽기)
  let body: BodyInit | undefined;
  let isMultipart = false;
  if (canHaveBody) {
    const contentType = request.headers.get('content-type');
    
    if (contentType?.includes('multipart/form-data')) {
      body = await request.formData();
      isMultipart = true;
    } else if (contentType?.includes('application/json')) {
      body = await request.text();
    } else {
      const text = await request.text();
      body = text || undefined;
    }
  }
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const url = new URL(request.url);
      const searchParams = url.searchParams.toString();
      const queryString = searchParams ? `?${searchParams}` : '';
      
      const backendUrl = `${BACKEND_URL}/api/${path}${queryString}`;
      console.log(`[API Proxy] 시도 ${attempt}/${maxRetries}: ${backendUrl}`);
      
      // 헤더 복사 (호스트 헤더 제외, multipart인 경우 Content-Type과 Content-Length도 제외)
      const headers = new Headers();
      request.headers.forEach((value, key) => {
        const lowerKey = key.toLowerCase();
        // multipart/form-data인 경우 Content-Type과 Content-Length 헤더를 제거
        // (FormData를 전달하면 브라우저가 자동으로 올바른 boundary와 함께 Content-Type을 설정함)
        if (lowerKey === 'host' || lowerKey === 'connection' || 
            (isMultipart && (lowerKey === 'content-type' || lowerKey === 'content-length'))) {
          return;
        }
        headers.set(key, value);
      });
      
      // multipart 요청은 재시도 불가능하므로 첫 번째 시도만 허용
      if (isMultipart && attempt > 1) {
        console.error('[API Proxy] multipart 요청은 재시도할 수 없습니다 (body가 이미 읽혔습니다)');
        return NextResponse.json(
          { 
            error: '파일 업로드 요청 실패', 
            message: lastError?.message || 'Unknown error'
          },
          { status: 503 }
        );
      }
      
      // 백엔드로 요청 전달 (타임아웃 설정)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30초 타임아웃
      
      try {
        console.log(`[API Proxy] 백엔드로 요청 전송: ${request.method} ${backendUrl}`);
        const response = await fetch(backendUrl, {
          method: request.method,
          headers,
          body: canHaveBody ? body : undefined,
          signal: controller.signal,
        });
        
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
      
      // multipart 요청은 재시도 불가능 (body가 이미 읽혔음)
      if (isMultipart) {
        console.error('[API Proxy] multipart 요청 실패 - 재시도 불가능');
        return NextResponse.json(
          { 
            error: '파일 업로드 요청 실패', 
            message: errorMessage,
            backendUrl: `${BACKEND_URL}/api/${pathSegments.join('/')}`,
          },
          { status: 503 }
        );
      }
      
      // ECONNREFUSED 오류인 경우 재시도 (multipart가 아닌 경우만)
      if (error instanceof Error && 
          (errorMessage.includes('ECONNREFUSED') || 
           errorMessage.includes('fetch failed'))) {
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
