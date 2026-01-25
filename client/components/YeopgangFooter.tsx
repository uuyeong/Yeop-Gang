"use client";

/**
 * Design Philosophy: Neo-Brutalism Meets Korean EdTech
 * - Structured footer with clear sections
 * - Bold borders and organized information
 */

export default function YeopgangFooter() {
  return (
    <footer className="bg-gray-900 text-white py-12 border-t border-gray-700">
      <div className="container">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Company Info */}
          <div>
            <h3 className="text-xl font-bold mb-4" style={{ fontFamily: 'var(--font-display)' }}>
              옆강
            </h3>
            <p className="text-sm text-gray-400">
              사이트 소개
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-bold mb-4">학습지원</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><button className="hover:text-white transition-colors">학습지원센터</button></li>
              <li><button className="hover:text-white transition-colors">이용가이드</button></li>
              <li><button className="hover:text-white transition-colors">FAQ</button></li>
              <li><button className="hover:text-white transition-colors">챗봇 상담</button></li>
            </ul>
          </div>

          {/* Services */}
          <div>
            <h4 className="font-bold mb-4">서비스</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><button className="hover:text-white transition-colors">옆강패스</button></li>
              <li><button className="hover:text-white transition-colors">온라인서점</button></li>
              <li><button className="hover:text-white transition-colors">문제은행</button></li>
              <li><button className="hover:text-white transition-colors">대입컨설팅</button></li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-bold mb-4">회사소개</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><button className="hover:text-white transition-colors">회사소개</button></li>
              <li><button className="hover:text-white transition-colors">인재채용</button></li>
              <li><button className="hover:text-white transition-colors">제휴문의</button></li>
              <li><button className="hover:text-white transition-colors">찾아오는길</button></li>
            </ul>
          </div>
        </div>

        {/* Contact Info */}
        <div className="border-t border-gray-700 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-sm text-gray-400">
            </div>
            <div className="flex gap-4 text-sm">
              <button className="hover:text-primary transition-colors">이용약관</button>
              <button className="hover:text-primary transition-colors font-bold">개인정보처리방침</button>
            </div>
          </div>
          <div className="mt-6 text-center text-sm text-gray-500">
            <p>© 2026 옆강. All rights reserved.</p>
          </div>
        </div>
      </div>
    </footer>
  );
}

