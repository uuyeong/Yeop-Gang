"use client";

import { useRef, useState, useImperativeHandle, forwardRef, useEffect, useCallback } from "react";
import { AlertCircle, Loader2, MoreVertical, Download, Type, EyeOff } from "lucide-react";
import { apiGet } from "../lib/api";

type Props = {
  src?: string;
  courseId?: string;
  onTimeUpdate?: (currentTime: number) => void;
};

type TranscriptSegment = {
  start: number;
  end: number;
  text: string;
};

export type VideoPlayerRef = {
  seekTo: (time: number) => void;
};

const VideoPlayer = forwardRef<VideoPlayerRef, Props>(({ src, courseId, onTimeUpdate }, ref) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [subtitlesEnabled, setSubtitlesEnabled] = useState(true); // 기본값: 켜짐
  const [subtitleData, setSubtitleData] = useState<TranscriptSegment[]>([]);
  const [currentSubtitle, setCurrentSubtitle] = useState<string>("");
  const [showSubtitleMenu, setShowSubtitleMenu] = useState(false);
  const [subtitleLoading, setSubtitleLoading] = useState(false);

  // 외부에서 호출 가능한 함수 노출
  useImperativeHandle(ref, () => ({
    seekTo: (time: number) => {
      if (videoRef.current) {
        videoRef.current.currentTime = time;
        setCurrentTime(time);
      }
    },
  }));

  const handleTimeUpdate = () => {
    if (videoRef.current && !isDragging) {
      const time = videoRef.current.currentTime;
      setCurrentTime(time);
      // 부모 컴포넌트에 현재 시간 전달
      if (onTimeUpdate) {
        onTimeUpdate(time);
      }
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
      setIsLoading(false);
      setError(null);
    }
  };

  const handleError = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    setIsLoading(false);
    const video = e.currentTarget;
    let errorMsg = "비디오를 로드할 수 없습니다.";
    
    if (video.error) {
      switch (video.error.code) {
        case video.error.MEDIA_ERR_ABORTED:
          errorMsg = "비디오 로드가 중단되었습니다.";
          break;
        case video.error.MEDIA_ERR_NETWORK:
          errorMsg = "네트워크 오류로 비디오를 로드할 수 없습니다.";
          break;
        case video.error.MEDIA_ERR_DECODE:
          errorMsg = "비디오 디코딩 오류가 발생했습니다.";
          break;
        case video.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
          errorMsg = "비디오 형식이 지원되지 않습니다.";
          break;
      }
    }
    setError(errorMsg);
    console.error("Video error:", video.error, "src:", src);
  };

  const handleLoadStart = () => {
    setIsLoading(true);
    setError(null);
  };

  // src가 변경되면 로딩 상태 초기화
  useEffect(() => {
    setIsLoading(true);
    setError(null);
  }, [src]);

  // 자막 데이터 로드 - 처음부터 다시 구현
  useEffect(() => {
    if (!courseId) {
      console.warn(`[자막] courseId가 없어서 자막 로드를 건너뜁니다.`);
      return;
    }

    const loadSubtitles = async () => {
      setSubtitleLoading(true);
      try {
        console.log(`[자막] ========== 자막 로드 시작 ==========`);
        console.log(`[자막] courseId: ${courseId}`);
        
        // 토큰 가져오기
        const token = typeof window !== 'undefined' 
          ? (localStorage.getItem("token") || localStorage.getItem("instructor_token") || localStorage.getItem("yeopgang_access_token") || "")
          : "";
        
        const endpoint = `/api/courses/${courseId}/transcript`;
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const fullUrl = `${apiBaseUrl}${endpoint}`;
        
        console.log(`[자막] 요청 URL: ${fullUrl}`);
        console.log(`[자막] 토큰 있음: ${!!token}`);
        
        // API 호출
        const response = await fetch(fullUrl, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {}),
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        console.log(`[자막] ========== API 응답 수신 ==========`);
        console.log(`[자막] 응답 데이터:`, data);
        console.log(`[자막] segments 존재: ${!!data?.segments}`);
        console.log(`[자막] segments 타입: ${Array.isArray(data?.segments) ? "Array" : typeof data?.segments}`);
        console.log(`[자막] segments 길이: ${data?.segments?.length || 0}`);
        
        // segments 확인 및 저장
        if (data && data.segments && Array.isArray(data.segments) && data.segments.length > 0) {
          // segments 정렬 (시작 시간 기준)
          const sortedSegments = [...data.segments].sort((a, b) => {
            const startA = typeof a.start === 'number' ? a.start : parseFloat(String(a.start || 0));
            const startB = typeof b.start === 'number' ? b.start : parseFloat(String(b.start || 0));
            return startA - startB;
          });
          
          console.log(`[자막] ✅ 자막 세그먼트 ${sortedSegments.length}개 로드 성공!`);
          console.log(`[자막] 첫 번째 세그먼트:`, sortedSegments[0]);
          console.log(`[자막] 마지막 세그먼트:`, sortedSegments[sortedSegments.length - 1]);
          
          setSubtitleData(sortedSegments);
          setSubtitlesEnabled(true); // 자막 데이터가 있으면 자동으로 켜기
          console.log(`[자막] ✅ 자막 데이터 설정 완료, 자동으로 켜짐`);
        } else {
          console.warn(`[자막] ⚠️ 자막 segments가 없거나 비어있습니다.`);
          console.warn(`[자막] data:`, data);
          setSubtitleData([]);
          setSubtitlesEnabled(false);
        }
      } catch (err: any) {
        console.error(`[자막] ❌ 자막 데이터 로드 실패:`, err);
        console.error(`[자막] 에러 메시지:`, err?.message || String(err));
        setSubtitleData([]);
        setSubtitlesEnabled(false);
      } finally {
        setSubtitleLoading(false);
      }
    };

    loadSubtitles();
  }, [courseId]);

  // 현재 시간에 맞는 자막 찾기 - 개선된 로직
  useEffect(() => {
    if (!subtitlesEnabled || subtitleData.length === 0) {
      setCurrentSubtitle("");
      return;
    }

    // 현재 재생 시간에 맞는 자막 찾기
    const findSubtitle = () => {
      // 이진 탐색으로 더 효율적으로 찾기
      let left = 0;
      let right = subtitleData.length - 1;
      let found: TranscriptSegment | null = null;

      while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        const segment = subtitleData[mid];
        const start = typeof segment.start === 'number' ? segment.start : parseFloat(String(segment.start || 0));
        const end = typeof segment.end === 'number' ? segment.end : parseFloat(String(segment.end || 0));

        if (currentTime >= start && currentTime < end) {
          found = segment;
          break;
        } else if (currentTime < start) {
          right = mid - 1;
        } else {
          left = mid + 1;
        }
      }

      // 이진 탐색으로 못 찾았으면 선형 탐색 (경계 케이스)
      if (!found) {
        found = subtitleData.find((seg) => {
          const start = typeof seg.start === 'number' ? seg.start : parseFloat(String(seg.start || 0));
          const end = typeof seg.end === 'number' ? seg.end : parseFloat(String(seg.end || 0));
          return currentTime >= start && currentTime < end;
        }) || null;
      }

      return found?.text || "";
    };

    const subtitleText = findSubtitle();
    if (subtitleText !== currentSubtitle) {
      setCurrentSubtitle(subtitleText);
      if (subtitleText) {
        console.log(`[자막 표시] ${currentTime.toFixed(2)}초: "${subtitleText.substring(0, 50)}..."`);
      }
    }
  }, [currentTime, subtitleData, subtitlesEnabled, currentSubtitle]);

  const toggleSubtitles = () => {
    setSubtitlesEnabled(!subtitlesEnabled);
    console.log(`[자막] ${!subtitlesEnabled ? '켜기' : '끄기'}`);
  };

  const handleDownload = () => {
    if (src) {
      const link = document.createElement("a");
      link.href = src;
      link.download = `video-${courseId || "download"}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setShowSubtitleMenu(false);
    }
  };

  const handleProgressChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value);
    setCurrentTime(newTime);
    if (videoRef.current) {
      videoRef.current.currentTime = newTime;
    }
  };

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="aspect-video w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm relative">
      {/* 로딩 상태 */}
      {isLoading && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900 z-10">
          <div className="flex flex-col items-center gap-3 text-white">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="text-sm">비디오 로딩 중...</span>
          </div>
        </div>
      )}

      {/* 에러 상태 */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900 z-10">
          <div className="flex flex-col items-center gap-3 text-white p-6 text-center">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <div>
              <p className="text-sm font-medium mb-1">{error}</p>
              <p className="text-xs text-slate-400">URL: {src}</p>
            </div>
            <button
              onClick={() => {
                setError(null);
                setIsLoading(true);
                if (videoRef.current) {
                  videoRef.current.load();
                }
              }}
              className="mt-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              다시 시도
            </button>
          </div>
        </div>
      )}

      <div className="relative group">
        <video
          ref={videoRef}
          className="h-full w-full bg-black"
          controls
          src={src ?? `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/video/default`}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onError={handleError}
          onLoadStart={handleLoadStart}
          preload="metadata"
          playsInline
        />
        
        {/* 자막 토글 버튼 (CC) - 비디오 우측 상단에 고정 */}
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            if (subtitleLoading || subtitleData.length === 0) {
              console.log(`[자막 토글] ⚠️ 자막이 없어서 토글 불가`);
              return;
            }
            const newState = !subtitlesEnabled;
            setSubtitlesEnabled(newState);
            console.log(`[자막 토글] ✅ 자막 상태 변경: ${subtitlesEnabled} → ${newState}`);
          }}
          disabled={subtitleLoading || subtitleData.length === 0}
          className={`absolute top-4 right-4 z-50 px-3 py-2 rounded-lg shadow-lg transition-all font-bold text-sm ${
            subtitleLoading || subtitleData.length === 0
              ? "bg-slate-500/50 text-slate-300 cursor-not-allowed opacity-50"
              : subtitlesEnabled
              ? "bg-white/90 text-blue-600 hover:bg-white hover:scale-110 border-2 border-blue-600"
              : "bg-black/70 text-white hover:bg-black/90 hover:scale-110 border border-white/30"
          }`}
          title={
            subtitleLoading 
              ? "자막 로딩 중..." 
              : subtitleData.length === 0 
              ? "자막 없음" 
              : subtitlesEnabled 
              ? "자막 끄기 (클릭)" 
              : "자막 켜기 (클릭)"
          }
        >
          CC
        </button>

        {/* 자막 표시 영역 - 비디오 위에 오버레이 */}
        {subtitlesEnabled && (
          <div className="absolute inset-0 pointer-events-none z-40 flex items-end justify-center pb-16">
            {currentSubtitle ? (
              <div className="px-6 py-3 mx-4 mb-4 bg-black/75 backdrop-blur-sm text-white text-lg rounded-lg max-w-[90%] text-center shadow-2xl border border-white/10">
                <span className="whitespace-pre-wrap break-words leading-relaxed">
                  {currentSubtitle}
                </span>
              </div>
            ) : subtitleLoading ? (
              <div className="px-4 py-2 bg-black/50 text-white text-sm rounded">
                자막 로딩 중...
              </div>
            ) : subtitleData.length === 0 ? (
              <div className="px-4 py-2 bg-black/50 text-white text-sm rounded">
                자막 없음
              </div>
            ) : null}
          </div>
        )}
      </div>
      {/* 커스텀 타임라인 컨트롤 */}
      <div className="relative w-full bg-slate-50 border-t border-slate-200 px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-600 min-w-[40px]">
            {formatTime(currentTime)}
          </span>
          <input
            type="range"
            min="0"
            max={duration || 0}
            step="0.1"
            value={currentTime}
            onChange={handleProgressChange}
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}
            onTouchStart={handleMouseDown}
            onTouchEnd={handleMouseUp}
            className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            style={{
              background: `linear-gradient(to right, rgb(37 99 235) 0%, rgb(37 99 235) ${
                duration ? (currentTime / duration) * 100 : 0
              }%, rgb(226 232 240) ${
                duration ? (currentTime / duration) * 100 : 0
              }%, rgb(226 232 240) 100%)`,
            }}
          />
          <span className="text-xs text-slate-600 min-w-[40px]">
            {formatTime(duration)}
          </span>
          {/* 자막 온오프 버튼 (CC) - 직접 접근 가능하도록 */}
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              const newState = !subtitlesEnabled;
              setSubtitlesEnabled(newState);
              console.log(`[자막 토글] ✅ 자막 상태 변경: ${subtitlesEnabled} → ${newState}`);
            }}
            disabled={subtitleLoading || subtitleData.length === 0}
            className={`px-2.5 py-1 rounded-lg transition-colors text-xs font-bold ${
              subtitleLoading || subtitleData.length === 0
                ? "text-slate-300 cursor-not-allowed"
                : subtitlesEnabled
                ? "text-blue-600 hover:bg-blue-50 bg-blue-50 border border-blue-300"
                : "text-slate-600 hover:bg-slate-200 border border-slate-300"
            }`}
            title={subtitleLoading ? "자막 로딩 중..." : subtitleData.length === 0 ? "자막 없음" : subtitlesEnabled ? "자막 끄기" : "자막 켜기"}
          >
            CC
          </button>
          {/* 점 세 개 메뉴 버튼 */}
          <div className="relative">
            <button
              onClick={() => setShowSubtitleMenu(!showSubtitleMenu)}
              className="p-1.5 rounded-lg hover:bg-slate-200 transition-colors"
              title="메뉴"
            >
              <MoreVertical className="h-4 w-4 text-slate-600" />
            </button>
            {showSubtitleMenu && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowSubtitleMenu(false)}
                />
                <div className="absolute bottom-full right-0 mb-2 bg-white border border-slate-200 rounded-lg shadow-xl py-1 z-50 min-w-[160px]">
                  <button
                    onClick={handleDownload}
                    className="w-full px-4 py-2 text-sm text-left hover:bg-slate-50 transition-colors flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>다운로드</span>
                  </button>
                  <div className="border-t border-slate-200 my-1"></div>
                  {/* 자막 온오프 버튼 */}
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      const newState = !subtitlesEnabled;
                      setSubtitlesEnabled(newState);
                      console.log(`[자막 메뉴] ✅ 자막 상태 변경: ${subtitlesEnabled} → ${newState}, 세그먼트 개수: ${subtitleData.length}`);
                      setShowSubtitleMenu(false);
                    }}
                    disabled={subtitleLoading}
                    className={`w-full px-4 py-2 text-sm text-left transition-colors flex items-center justify-between gap-2 ${
                      subtitleLoading 
                        ? "text-slate-400 cursor-not-allowed" 
                        : "hover:bg-slate-50 text-slate-900 cursor-pointer"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`font-bold text-xs px-1.5 py-0.5 rounded ${
                        subtitlesEnabled 
                          ? "bg-blue-100 text-blue-700 border border-blue-300" 
                          : "bg-slate-100 text-slate-600 border border-slate-300"
                      }`}>
                        CC
                      </span>
                      <span>{subtitlesEnabled ? "자막 끄기" : "자막 켜기"}</span>
                    </div>
                    {subtitleLoading ? (
                      <span className="text-xs text-slate-400">(로딩 중...)</span>
                    ) : subtitleData.length > 0 ? (
                      <span className={`text-xs font-medium ${subtitlesEnabled ? "text-green-600" : "text-slate-500"}`}>
                        ({subtitleData.length}개)
                      </span>
                    ) : (
                      <span className="text-xs text-slate-400">(없음)</span>
                    )}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});

VideoPlayer.displayName = "VideoPlayer";

export default VideoPlayer;
