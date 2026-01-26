"use client";

import { BookOpen, UserPlus, Upload, MessageSquare, FileText, HelpCircle, GraduationCap, Video, Brain, CheckCircle } from "lucide-react";
import Link from "next/link";

export default function GuidePage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 sm:px-6 py-8 sm:py-12 md:py-16">
        {/* 헤더 */}
        <div className="text-center mb-8 sm:mb-12 md:mb-16">
          <div className="inline-flex items-center justify-center w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-blue-100 text-blue-600 mb-4 sm:mb-6">
            <HelpCircle className="h-6 w-6 sm:h-8 sm:w-8" />
          </div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 mb-2 sm:mb-4" style={{ fontFamily: 'var(--font-display)' }}>
            이용안내
          </h1>
          <p className="text-sm sm:text-base md:text-lg text-slate-600 px-4">
            옆강의 다양한 기능을 쉽고 빠르게 이용하세요
          </p>
        </div>

        {/* 강사 회원가입 */}
        <section className="mb-8 sm:mb-12 md:mb-16">
          <div className="bg-white rounded-2xl border-2 border-gray-300 p-4 sm:p-6 md:p-8 shadow-sm">
            <div className="mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                <span className="text-blue-500 mr-2">A.</span>강사 회원가입
              </h2>
            </div>
            <div className="space-y-3 sm:space-y-4 text-slate-700">
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">1. 회원가입</p>
                  <p className="text-xs sm:text-sm text-slate-600">상단 헤더의 "회원가입" 버튼을 클릭하고 강사 역할을 선택합니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">2. 정보 입력</p>
                  <p className="text-xs sm:text-sm text-slate-600">사용자 ID, 비밀번호, 이름, 이메일, 전문 분야, 자기소개를 입력합니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">3. 가입 완료</p>
                  <p className="text-xs sm:text-sm text-slate-600">가입이 완료되면 로그인하여 강의를 업로드할 수 있습니다.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 강의 업로드 */}
        <section className="mb-8 sm:mb-12 md:mb-16">
          <div className="bg-white rounded-2xl border-2 border-gray-300 p-4 sm:p-6 md:p-8 shadow-sm">
            <div className="mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                <span className="text-blue-500 mr-2">B.</span>강의 업로드
              </h2>
            </div>
            <div className="space-y-3 sm:space-y-4 text-slate-700">
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">1. 강의 정보 입력</p>
                  <p className="text-xs sm:text-sm text-slate-600">강의 제목, 카테고리(과목), 설명을 입력합니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">2. 영상 파일 업로드</p>
                  <p className="text-xs sm:text-sm text-slate-600">강의 영상 파일을 업로드합니다. (MP4, MOV 등 지원)</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">3. 자동 처리</p>
                  <p className="text-xs sm:text-sm text-slate-600">
                    <span className="font-medium">STT (음성 인식):</span> 영상의 음성을 자동으로 텍스트로 변환합니다.
                    <br />
                    <span className="font-medium">SMI 자막:</span> SMI 자막 파일이 있으면 함께 업로드할 수 있습니다.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">4. 챕터 구성</p>
                  <p className="text-xs sm:text-sm text-slate-600">강의를 여러 챕터로 나누어 구성할 수 있습니다.</p>
                </div>
              </div>
            </div>
            <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-xs sm:text-sm text-blue-800">
                💡 <span className="font-medium">팁:</span> STT 처리가 완료되면 자동으로 강의 내용이 분석되어 챗봇과 요약 기능에 활용됩니다.
              </p>
            </div>
          </div>
        </section>

        {/* 챗봇 기능 */}
        <section className="mb-8 sm:mb-12 md:mb-16">
          <div className="bg-white rounded-2xl border-2 border-gray-300 p-4 sm:p-6 md:p-8 shadow-sm">
            <div className="mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                <span className="text-blue-500 mr-2">C.</span>AI 챗봇 기능
              </h2>
            </div>
            <div className="space-y-3 sm:space-y-4 text-slate-700">
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">강의 내용 질문</p>
                  <p className="text-xs sm:text-sm text-slate-600">강의를 시청하면서 궁금한 내용을 AI 챗봇에게 질문할 수 있습니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">맥락 이해</p>
                  <p className="text-xs sm:text-sm text-slate-600">AI가 강의 내용을 이해하고 정확한 답변을 제공합니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">실시간 상담</p>
                  <p className="text-xs sm:text-sm text-slate-600">강의 재생 중 언제든지 채팅창을 열어 질문할 수 있습니다.</p>
                </div>
              </div>
            </div>
            <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-xs sm:text-sm text-blue-800">
                💡 <span className="font-medium">팁:</span> "이 부분 설명해줘", "핵심 개념 정리해줘" 등 자연스러운 질문으로 이용하세요.
              </p>
            </div>
          </div>
        </section>

        {/* 요약 기능 */}
        <section className="mb-8 sm:mb-12 md:mb-16">
          <div className="bg-white rounded-2xl border-2 border-gray-300 p-4 sm:p-6 md:p-8 shadow-sm">
            <div className="mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                <span className="text-blue-500 mr-2">D.</span>자동 요약 기능
              </h2>
            </div>
            <div className="space-y-3 sm:space-y-4 text-slate-700">
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">자동 요약 생성</p>
                  <p className="text-xs sm:text-sm text-slate-600">강의 내용을 AI가 자동으로 분석하여 핵심 내용을 요약합니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">챕터별 요약</p>
                  <p className="text-xs sm:text-sm text-slate-600">각 챕터마다 별도의 요약 노트가 생성되어 복습에 활용할 수 있습니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">저장 및 관리</p>
                  <p className="text-xs sm:text-sm text-slate-600">생성된 요약 노트를 저장하고 나중에 다시 확인할 수 있습니다.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 퀴즈 기능 */}
        <section className="mb-8 sm:mb-12 md:mb-16">
          <div className="bg-white rounded-2xl border-2 border-gray-300 p-4 sm:p-6 md:p-8 shadow-sm">
            <div className="mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                <span className="text-blue-500 mr-2">E.</span>AI 퀴즈 생성
              </h2>
            </div>
            <div className="space-y-3 sm:space-y-4 text-slate-700">
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">자동 퀴즈 생성</p>
                  <p className="text-xs sm:text-sm text-slate-600">강의 내용을 바탕으로 AI가 자동으로 퀴즈 문제를 생성합니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">다양한 문제 유형</p>
                  <p className="text-xs sm:text-sm text-slate-600">객관식, 주관식 등 다양한 형태의 문제가 생성됩니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">즉시 채점</p>
                  <p className="text-xs sm:text-sm text-slate-600">답안을 제출하면 즉시 채점 결과와 해설을 확인할 수 있습니다.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 학생 이용 방법 */}
        <section className="mb-8 sm:mb-12 md:mb-16">
          <div className="bg-white rounded-2xl border-2 border-gray-300 p-4 sm:p-6 md:p-8 shadow-sm">
            <div className="mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                <span className="text-blue-500 mr-2">F.</span>학생 이용 방법
              </h2>
            </div>
            <div className="space-y-3 sm:space-y-4 text-slate-700">
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">1. 강의 찾기</p>
                  <p className="text-xs sm:text-sm text-slate-600">"모든 강좌" 또는 "선생님" 메뉴에서 원하는 강의를 찾습니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">2. 강의 수강</p>
                  <p className="text-xs sm:text-sm text-slate-600">강의를 선택하고 챕터별로 수강합니다.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1 text-sm sm:text-base">3. 기능 활용</p>
                  <p className="text-xs sm:text-sm text-slate-600">강의 시청 중 챗봇, 요약, 퀴즈 기능을 활용하여 학습 효과를 높입니다.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <div className="text-center">
          <Link
            href="/student/courses/all"
            className="inline-flex items-center gap-2 px-6 sm:px-8 py-3 sm:py-4 bg-primary text-white rounded-lg font-bold text-base sm:text-lg hover:bg-secondary transition-all duration-150"
          >
            <BookOpen className="h-4 w-4 sm:h-5 sm:w-5" />
            <span>강의 둘러보기</span>
          </Link>
        </div>
      </div>
    </main>
  );
}

