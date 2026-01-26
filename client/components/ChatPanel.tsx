"use client";

import { useMemo, useState, useRef, useEffect } from "react";
import { AlertCircle } from "lucide-react";
import type { ChatMessage } from "../lib/types";
import { API_BASE_URL, apiPost, apiGet, handleApiError } from "../lib/api";

type Props = {
  courseId: string;
  courseTitle?: string;  // 강의명 (선택사항)
  instructorName?: string;  // 강사명 (선택사항)
  instructorProfileImageUrl?: string | null;  // 강사 프로필 이미지 URL (선택사항)
  onTimestampClick?: (timeInSeconds: number) => void;
  currentTime?: number;  // 현재 비디오 재생 시간 (초)
};

export default function ChatPanel({ courseId, courseTitle, instructorName, instructorProfileImageUrl, onTimestampClick, currentTime }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<{ message: string; retryQuestion?: string } | null>(null);
  const [conversationId] = useState(() => `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [greetingLoaded, setGreetingLoaded] = useState(false);

  // 초기 인사말 로드
  useEffect(() => {
    const loadGreeting = async () => {
      if (greetingLoaded) return;
      
      try {
        const encodedCourseId = encodeURIComponent(courseId);
        const data = await apiGet<{ answer: string }>(
          `/api/chat/greeting?course_id=${encodedCourseId}`
        );
        
        if (data.answer) {
          setMessages([
            {
              role: "assistant",
              content: data.answer,
            },
          ]);
          setGreetingLoaded(true);
        } else {
          // API 실패 시 기본 인사말 사용
          setMessages([
            {
              role: "assistant",
              content: `안녕하세요! 강의에 대해 궁금한 점이 있으시면 언제든지 질문해 주세요.`,
            },
          ]);
          setGreetingLoaded(true);
        }
      } catch (error) {
        // API 실패 시 기본 인사말 사용
        console.error("Failed to load greeting:", error);
        setMessages([
          {
            role: "assistant",
            content: `안녕하세요! 강의에 대해 궁금한 점이 있으시면 언제든지 질문해 주세요.`,
          },
        ]);
        setGreetingLoaded(true);
      }
    };

    loadGreeting();
  }, [courseId, greetingLoaded]);

  const handleSend = async (question?: string) => {
    const trimmed = question || input.trim();
    if (!trimmed || isLoading) return;

    // 에러 상태 초기화
    setError(null);

    // 사용자 메시지 즉시 추가
    const userMessage: ChatMessage = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    if (!question) {
      setInput("");
    }
    setIsLoading(true);

    try {
      const data = await apiPost<{ answer: string; sources?: string[] }>(
        "/api/chat/ask",
        {
          course_id: courseId,
          question: trimmed,
          conversation_id: conversationId,
          current_time: currentTime || 0,  // 현재 시청 시간 전달
        }
      );

      // 답변이 너무 길면 여러 말풍선으로 나누기
      const answerText = data.answer || "답변을 받을 수 없습니다.";
      
      // 답변이 250자 이상이면 나누기 (더 적극적으로)
      if (answerText.length > 250) {
        // 먼저 빈 줄로 구분된 단락으로 나누기
        const paragraphs = answerText.split(/\n\n+/);
        
        if (paragraphs.length > 1) {
          // 빈 줄로 구분된 문단이 있으면 각 문단을 개별 메시지로 추가
          paragraphs.forEach((paragraph) => {
            const trimmedParagraph = paragraph.trim();
            if (trimmedParagraph) {
              // 문단이 250자 이상이면 문장 단위로 더 나누기
              if (trimmedParagraph.length > 250) {
                const sentences = trimmedParagraph.split(/([。.!?]\s*)/);
                const chunks: string[] = [];
                let currentChunk = "";
                
                for (let i = 0; i < sentences.length; i++) {
                  const sentence = sentences[i];
                  if (currentChunk.length + sentence.length + 1 < 250) {
                    currentChunk += (sentence + (currentChunk ? " " : ""));
                  } else {
                    if (currentChunk.trim()) {
                      chunks.push(currentChunk.trim());
                    }
                    currentChunk = sentence;
                  }
                }
                if (currentChunk.trim()) {
                  chunks.push(currentChunk.trim());
                }
                
                // 나눈 청크들을 각각 메시지로 추가
                chunks.forEach((chunk) => {
                  const assistantMessage: ChatMessage = {
                    role: "assistant",
                    content: chunk,
                  };
                  setMessages((prev) => [...prev, assistantMessage]);
                });
              } else {
                // 문단이 250자 이하면 그대로 추가
                const assistantMessage: ChatMessage = {
                  role: "assistant",
                  content: trimmedParagraph,
                };
                setMessages((prev) => [...prev, assistantMessage]);
              }
            }
          });
        } else {
          // 빈 줄이 없어도 250자 이상이면 문장 단위로 나누기
          const sentences = answerText.split(/([。.!?]\s*)/);
          const chunks: string[] = [];
          let currentChunk = "";
          
          for (let i = 0; i < sentences.length; i++) {
            const sentence = sentences[i];
            if (currentChunk.length + sentence.length + 1 < 250) {
              currentChunk += (sentence + (currentChunk ? " " : ""));
            } else {
              if (currentChunk.trim()) {
                chunks.push(currentChunk.trim());
              }
              currentChunk = sentence;
            }
          }
          if (currentChunk.trim()) {
            chunks.push(currentChunk.trim());
          }
          
          if (chunks.length > 1) {
            chunks.forEach((chunk) => {
              const assistantMessage: ChatMessage = {
                role: "assistant",
                content: chunk,
              };
              setMessages((prev) => [...prev, assistantMessage]);
            });
          } else {
            // 나눌 수 없으면 그대로 추가
            const assistantMessage: ChatMessage = {
              role: "assistant",
              content: answerText,
            };
            setMessages((prev) => [...prev, assistantMessage]);
          }
        }
      } else {
        // 답변이 250자 이하면 그대로 추가
        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: answerText,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error("채팅 API 오류:", error);
      
      const apiError = handleApiError(error);
      const errorMsg = apiError.message;

      // 에러 상태 저장 (재시도용)
      setError({
        message: errorMsg,
        retryQuestion: trimmed,
      });

      const errorMessage: ChatMessage = {
        role: "assistant",
        content: errorMsg,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    if (error?.retryQuestion) {
      handleSend(error.retryQuestion);
    }
  };

  // 마크다운 문법 제거 함수
  const removeMarkdown = (text: string): string => {
    return text
      // **볼드** 제거
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      // *이탤릭* 제거
      .replace(/\*([^*]+)\*/g, '$1')
      // __볼드__ 제거
      .replace(/__([^_]+)__/g, '$1')
      // _이탤릭_ 제거
      .replace(/_([^_]+)_/g, '$1')
      // # 헤딩 제거
      .replace(/^#{1,6}\s+/gm, '')
      // ~~취소선~~ 제거
      .replace(/~~([^~]+)~~/g, '$1')
      // `코드` 제거
      .replace(/`([^`]+)`/g, '$1')
      // [링크](url) 제거
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
      // 남은 마크다운 특수문자 제거
      .replace(/\*\*/g, '')
      .replace(/\*/g, '')
      .replace(/__/g, '')
      .replace(/_/g, '');
  };

  // 타임스탬프 파싱 및 렌더링 함수
  const parseAndRenderContent = (content: string) => {
    // 마크다운 문법 제거
    const cleanContent = removeMarkdown(content);
    
    // 타임스탬프 패턴: [파일명 @ 숫자s] 또는 @ 숫자s
    const timestampPattern = /(?:\[[^\]]*@\s*(\d+(?:\.\d+)?)s\]|@\s*(\d+(?:\.\d+)?)s)/g;
    const parts: (string | { type: "timestamp"; time: number; text: string })[] = [];
    let lastIndex = 0;
    let match;

    while ((match = timestampPattern.exec(cleanContent)) !== null) {
      // 타임스탬프 이전 텍스트 추가
      if (match.index > lastIndex) {
        parts.push(cleanContent.substring(lastIndex, match.index));
      }

      // 타임스탬프 추출 (첫 번째 그룹 또는 두 번째 그룹)
      const timeInSeconds = parseFloat(match[1] || match[2]);
      const fullMatch = match[0];

      // 시간을 분:초 형식으로 변환
      const minutes = Math.floor(timeInSeconds / 60);
      const seconds = Math.floor(timeInSeconds % 60);
      const timeText = `${minutes}:${seconds.toString().padStart(2, "0")}`;

      parts.push({
        type: "timestamp",
        time: timeInSeconds,
        text: fullMatch,
      });

      lastIndex = match.index + fullMatch.length;
    }

    // 마지막 텍스트 추가
    if (lastIndex < cleanContent.length) {
      parts.push(cleanContent.substring(lastIndex));
    }

    return parts.length > 0 ? parts : [cleanContent];
  };

  const handleTimestampClick = (timeInSeconds: number) => {
    if (onTimestampClick) {
      onTimestampClick(timeInSeconds);
    }
  };

  // 메시지가 추가될 때 자동 스크롤 (컨테이너 내부만)
  useEffect(() => {
    if (messagesContainerRef.current && messagesEndRef.current) {
      // 컨테이너 내부만 스크롤 (페이지 전체 스크롤 방지)
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages]);

  const transcript = useMemo(
    () => messages.map((m, idx) => ({ ...m, id: `msg-${idx}` })),
    [messages],
  );

  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-900">
        실시간 채팅
      </div>
      <div
        ref={messagesContainerRef}
        className="flex-1 space-y-2 overflow-y-auto px-3 py-3 bg-slate-100"
      >
        {transcript.map((msg, idx) => {
          return (
            <div
              key={msg.id}
              className={`flex gap-2 ${
                msg.role === "user" 
                  ? "flex-row-reverse items-end" 
                  : "items-start"
              }`}
            >
              {/* 프로필 이미지 (assistant만) */}
              {msg.role === "assistant" && (
                <div className="flex-shrink-0">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={instructorProfileImageUrl || "https://i.ibb.co/27yY0pLS/default-profile.png"}
                    alt={instructorName || "선생님"}
                    className="h-8 w-8 rounded-full object-cover border border-slate-200"
                  />
                </div>
              )}
              
              {/* 말풍선 영역 */}
              {msg.role === "assistant" ? (
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-slate-500 px-1">
                    {instructorName || "선생님"}
                  </span>
                  <div
                    className="rounded-2xl bg-white rounded-bl-sm px-3 py-2 max-w-[75%] shadow-sm"
                  >
                    <div className="text-sm">
                      {parseAndRenderContent(msg.content).map((part, idx) => {
                        if (typeof part === "string") {
                          return <span key={idx}>{part}</span>;
                        } else {
                          // 타임스탬프 버튼
                          const minutes = Math.floor(part.time / 60);
                          const seconds = Math.floor(part.time % 60);
                          const timeText = `${minutes}:${seconds.toString().padStart(2, "0")}`;
                          return (
                            <button
                              key={idx}
                              onClick={() => handleTimestampClick(part.time)}
                              className="mx-1 inline-flex items-center rounded-md bg-blue-500 px-2 py-0.5 text-xs font-medium text-white hover:bg-blue-600 transition-colors underline"
                              title={`${timeText}로 이동`}
                            >
                              {timeText}
                            </button>
                          );
                        }
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                <div
                  className="rounded-2xl bg-blue-500 text-white rounded-br-sm px-3 py-2 max-w-[75%]"
                >
                  <div className="text-sm text-white">
                    {removeMarkdown(msg.content)}
                  </div>
                </div>
              )}
            </div>
          );
        })}
        
        {/* 로딩 인디케이터 */}
        {isLoading && (
          <div className="flex items-start gap-2">
            <div className="flex-shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={instructorProfileImageUrl || "https://i.ibb.co/27yY0pLS/default-profile.png"}
                alt={instructorName || "선생님"}
                className="h-8 w-8 rounded-full object-cover border border-slate-200"
              />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs text-slate-500 px-1">{instructorName || "선생님"}</span>
              <div className="bg-white border border-slate-200 rounded-2xl px-4 py-2.5 shadow-sm">
                <div className="flex items-center gap-2 text-slate-500">
                  <div className="flex gap-1">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:-0.3s]"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:-0.15s]"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-blue-500"></div>
                  </div>
                  <span className="text-xs">답변 생성 중...</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* 스크롤 앵커 */}
        <div ref={messagesEndRef} />
      </div>
      
      {/* 에러 메시지 및 재시도 버튼 */}
      {error && (
        <div className="border-t border-red-200 bg-red-50 px-4 py-2">
          <div className="mb-2 flex items-center gap-2 text-xs text-red-700">
            <AlertCircle className="w-4 h-4" />
            {error.message}
          </div>
          <button
            onClick={handleRetry}
            className="w-full rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 transition-colors"
          >
            다시 시도
          </button>
        </div>
      )}
      
      <div className="border-t border-slate-200 bg-slate-50 p-3">
        <div className="flex gap-2">
          <input
            className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
            placeholder={isLoading ? "답변 대기 중..." : "질문을 입력하세요..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !isLoading && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={isLoading}
          />
          <button
            className="rounded-lg bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
          >
            {isLoading ? "전송 중..." : "전송"}
          </button>
        </div>
      </div>
    </div>
  );
}