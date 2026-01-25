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
    
    // 백엔드로 요청 전달
    const response = await fetch(backendUrl, {
      method: request.method,
      headers,
      body,
    });
    
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
  } catch (error) {
    console.error('[AI Proxy] Error:', error);
    return NextResponse.json(
      { 
        error: '프록시 요청 실패', 
        message: error instanceof Error ? error.message : 'Unknown error',
        details: process.env.NODE_ENV === 'development' ? String(error) : undefined
      },
      { status: 500 }
    );
  }
}
