/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    // typedRoutes: true, // 동적 경로 사용 시 타입 오류 발생 가능
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // 외부 배포 시 rewrites는 필요 없음 (NEXT_PUBLIC_API_URL로 직접 연결)
  // 로컬 개발 시에만 rewrites 사용 (선택사항)
};

export default nextConfig;

