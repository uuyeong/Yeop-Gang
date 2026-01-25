/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    typedRoutes: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Render 환경에서 백엔드 API 프록시 (같은 컨테이너 내에서 실행)
  // 클라이언트 사이드 요청을 백엔드로 프록시
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
      {
        source: "/ai/:path*",
        destination: "http://localhost:8000/ai/:path*",
      },
    ];
  },
};

export default nextConfig;

