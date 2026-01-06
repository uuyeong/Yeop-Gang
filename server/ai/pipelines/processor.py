"""
백엔드 A: 자동화 파이프라인 오케스트레이션
- STT → PDF 처리 → 페르소나 추출 → RAG 인제스트
- 순수 AI 처리 로직만 담당 (DB 작업 제외)
"""
from pathlib import Path
from typing import Optional, List, Dict, Any

from ai.config import AISettings
from ai.pipelines.rag import RAGPipeline
from ai.services.stt import transcribe_video


def process_course_assets(
    *,
    course_id: str,
    instructor_id: str,
    video_path: Optional[Path] = None,
    audio_path: Optional[Path] = None,
    pdf_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    백엔드 A: 자동화 파이프라인 오케스트레이션
    
    Background pipeline: STT → PDF 처리 → 페르소나 추출 → RAG 인제스트
    
    이 함수는 순수 AI 처리 로직만 담당합니다.
    DB 작업(Course, Video 모델 생성 등)은 백엔드 B의 책임입니다.
    
    Args:
        course_id: 강의 ID
        instructor_id: 강사 ID
        video_path: 비디오/오디오 파일 경로 (선택적)
        audio_path: 오디오 파일 경로 (선택적)
        pdf_path: PDF 파일 경로 (선택적)
    
    Returns:
        {
            "status": "completed" | "error",
            "ingested_count": int,
            "error": str (optional)
        }
    """
    settings = AISettings()
    pipeline = RAGPipeline(settings)
    
    try:
        texts: List[str] = []
        ingested_count = 0
        
        # 1. 비디오/오디오 STT 처리
        # video_path 또는 audio_path 중 하나를 사용 (둘 다 있으면 video_path 우선)
        media_path = video_path or audio_path
        if media_path and media_path.exists():
            try:
                print(f"[{course_id}] 🎤 STT 처리 시작: {media_path.name}")
                transcript_result = transcribe_video(str(media_path), settings=settings)
                transcript_text = transcript_result.get("text", "")
                segments = transcript_result.get("segments", [])
                
                if transcript_text:
                    # 병합 텍스트 전체를 persona 생성용 샘플에 추가
                    texts.append(transcript_text)
                    
                    # 세그먼트별 메타데이터 포함하여 RAG 인제스트
                    print(f"[{course_id}] 📝 {len(segments)}개 세그먼트 인제스트 시작...")
                    for idx, seg in enumerate(segments):
                        seg_text = seg.get("text", "")
                        if not seg_text:
                            continue
                        
                        seg_meta = {
                            "course_id": course_id,
                            "instructor_id": instructor_id,
                            "source": media_path.name,
                            "start_time": seg.get("start"),
                            "end_time": seg.get("end"),
                            "segment_index": idx,
                            "type": "video_segment" if video_path else "audio_segment",
                        }
                        
                        result = pipeline.ingest_texts(
                            [seg_text],
                            course_id=course_id,
                            metadata=seg_meta,
                        )
                        ingested_count += result.get("ingested", 0)
                    
                    print(f"[{course_id}] ✅ 세그먼트 인제스트 완료")
                else:
                    print(f"[{course_id}] ⚠️ STT 결과 텍스트가 비어있습니다: {media_path.name}")
                    
            except Exception as e:
                error_msg = f"[{course_id}] ❌ STT 처리 오류 ({media_path.name}): {str(e)}"
                print(error_msg)
                # 오류가 발생해도 계속 진행
        
        # 2. PDF 멀티모달 처리 (텍스트 + 이미지 설명)
        if pdf_path and pdf_path.exists():
            try:
                print(f"[{course_id}] 📄 PDF 멀티모달 처리 시작: {pdf_path.name}")
                # PDF 처리 모듈이 있으면 사용, 없으면 스킵
                try:
                    from ai.services.pdf import extract_pdf_content
                    pdf_result = extract_pdf_content(str(pdf_path), settings=settings, extract_images=True)
                    pdf_texts = pdf_result.get("texts", [])
                    pdf_metadata_list = pdf_result.get("metadata", [])
                    
                    if pdf_texts:
                        # PDF 텍스트를 persona 생성용 샘플에 추가
                        texts.extend(pdf_texts)
                        
                        # 페이지별로 개별 RAG 인제스트 (페이지 번호 등 메타데이터 포함)
                        print(f"[{course_id}] 🖼️ PDF {len(pdf_texts)}개 페이지 인제스트 시작...")
                        for pdf_text, pdf_meta in zip(pdf_texts, pdf_metadata_list):
                            page_meta = {
                                "course_id": course_id,
                                "instructor_id": instructor_id,
                                "source": pdf_path.name,
                                "page_number": pdf_meta.get("page_number"),
                                "type": "pdf_page",
                            }
                            
                            result = pipeline.ingest_texts(
                                [pdf_text],
                                course_id=course_id,
                                metadata=page_meta,
                            )
                            ingested_count += result.get("ingested", 0)
                        
                        print(f"[{course_id}] ✅ PDF 페이지 인제스트 완료")
                    else:
                        print(f"[{course_id}] ⚠️ PDF에서 텍스트를 추출하지 못했습니다: {pdf_path.name}")
                except ImportError:
                    print(f"[{course_id}] ⚠️ PDF 처리 모듈이 없습니다. PDF 처리를 건너뜁니다.")
                    # PDF 처리 모듈이 없어도 계속 진행
                        
            except Exception as e:
                error_msg = f"[{course_id}] ❌ PDF 처리 오류 ({pdf_path.name}): {str(e)}"
                print(error_msg)
                # 오류가 발생해도 계속 진행
        
        # 3. 페르소나 추출 및 RAG 인제스트
        if texts:
            print(f"[{course_id}] 🧑‍🏫 페르소나 추출 시작...")
            # 동적 페르소나 프롬프트 생성
            try:
                persona_prompt = pipeline.generate_persona_prompt(
                    course_id=course_id, sample_texts=texts
                )
                
                # 페르소나 프롬프트를 벡터 DB에 저장
                result = pipeline.ingest_texts(
                    [persona_prompt],
                    course_id=course_id,
                    metadata={
                        "course_id": course_id,
                        "instructor_id": instructor_id,
                        "type": "persona",
                    },
                )
                ingested_count += result.get("ingested", 0)
                print(f"[{course_id}] ✅ 페르소나 추출 및 저장 완료")
                
            except Exception as e:
                error_msg = f"[{course_id}] ❌ 페르소나 추출 오류: {str(e)}"
                print(error_msg)
                # 페르소나 추출 실패해도 계속 진행
        else:
            print(f"[{course_id}] ⚠️ 처리할 텍스트가 없습니다.")
        
        return {
            "status": "completed",
            "ingested_count": ingested_count,
        }
        
    except Exception as e:
        error_msg = f"[{course_id}] ❌ 파이프라인 오케스트레이션 오류: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "ingested_count": ingested_count if 'ingested_count' in locals() else 0,
            "error": error_msg,
        }
