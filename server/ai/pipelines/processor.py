"""
백엔드 A: 자동화 파이프라인 오케스트레이션
- STT → PDF 처리 → 페르소나 추출 → RAG 인제스트
- 순수 AI 처리 로직만 담당 (DB 작업 제외)
"""
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

from ai.config import AISettings
from ai.pipelines.rag import RAGPipeline
from ai.services.stt import transcribe_video
from ai.style_analyzer import analyze_instructor_style
import json
import hashlib


def process_course_assets(
    *,
    course_id: str,
    instructor_id: str,
    video_path: Optional[Path] = None,
    audio_path: Optional[Path] = None,
    pdf_path: Optional[Path] = None,
    smi_path: Optional[Path] = None,
    update_progress: Optional[Callable[[int, str], None]] = None,
    instructor_info: Optional[Dict[str, Any]] = None,
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
        smi_path: SMI 자막 파일 경로 (선택적, 제공 시 STT를 건너뜀)
        update_progress: 진행률 업데이트 콜백 함수 (progress: int, message: str) -> None
    
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
        persona_profile_json = None  # Style Analyzer 결과 (초기화)

        # 1. Transcript 생성 (SMI 우선, 없으면 STT)
        # SMI가 있으면 STT를 건너뛰고 자막을 transcript로 사용
        transcript_text = ""
        segments: List[Dict[str, Any]] = []
        transcript_path = None

        # SMI 경로 정규화/대체 경로 탐색
        if smi_path:
            if not isinstance(smi_path, Path):
                smi_path = Path(smi_path)
            if not smi_path.is_absolute():
                smi_path = smi_path.resolve()
            print(f"[{course_id}] 📁 SMI path: {smi_path}")
            print(f"[{course_id}] 📁 SMI exists: {smi_path.exists()}")

            if not smi_path.exists():
                try:
                    from core.config import AppSettings
                    app_settings = AppSettings()
                    potential_path = app_settings.uploads_dir / instructor_id / course_id / smi_path.name
                    if potential_path.exists():
                        smi_path = potential_path.resolve()
                        print(f"[{course_id}] 📁 Found SMI at alternative path: {smi_path}")
                    else:
                        raise FileNotFoundError(f"SMI file not found: {smi_path} (also tried: {potential_path})")
                except Exception as e:
                    print(f"[{course_id}] ❌ Error finding SMI file: {e}")
                    raise

        # STT용 media_path 정규화 (SMI가 없을 때만 사용)
        # 비디오는 프론트엔드 영상 출력용이므로 STT하지 않음 (오디오 파일만 STT)
        media_path = audio_path  # video_path는 STT에서 제외
        
        # 경로를 절대 경로로 변환
        if media_path:
            if not isinstance(media_path, Path):
                media_path = Path(media_path)
            if not media_path.is_absolute():
                media_path = media_path.resolve()
            print(f"[{course_id}] 📁 Media path: {media_path}")
            print(f"[{course_id}] 📁 Media exists: {media_path.exists()}")
            
            # 파일이 없으면 대체 경로 시도
            if not media_path.exists():
                try:
                    from core.config import AppSettings
                    app_settings = AppSettings()
                    potential_path = app_settings.uploads_dir / instructor_id / course_id / media_path.name
                    if potential_path.exists():
                        media_path = potential_path.resolve()
                        print(f"[{course_id}] 📁 Found media at alternative path: {media_path}")
                    else:
                        print(f"[{course_id}] ❌ Media file not found: {media_path} (also tried: {potential_path})")
                        raise FileNotFoundError(f"Media file not found: {media_path}")
                except Exception as e:
                    print(f"[{course_id}] ❌ Error finding media file: {e}")
                    raise
        
        # SMI가 있으면 여기서 transcript 생성/저장
        if smi_path and smi_path.exists():
            try:
                from ai.services.smi_parser import parse_smi_file
                import json
                from core.config import AppSettings

                if update_progress:
                    update_progress(15, "SMI 자막 파일 파싱 중...")
                print(f"[{course_id}] 📝 SMI 자막 기반 transcript 생성 시작: {smi_path.name}")
                transcript_result = parse_smi_file(smi_path)
                transcript_text = transcript_result.get("text", "") or ""
                segments = transcript_result.get("segments", []) or []
                print(f"[{course_id}] ✅ SMI parsed - text length: {len(transcript_text)}, segments: {len(segments)}")
                
                if update_progress:
                    update_progress(30, "SMI 자막 파싱 완료, 세그먼트 임베딩 준비 중...")

                if not transcript_text.strip():
                    raise ValueError(f"[{course_id}] ❌ SMI 파싱 결과 텍스트가 비어있습니다.")

                app_settings = AppSettings()
                course_dir = app_settings.uploads_dir / instructor_id / course_id
                course_dir.mkdir(parents=True, exist_ok=True)

                transcript_filename = f"transcript_{smi_path.stem}.json"
                transcript_file_path = course_dir / transcript_filename

                transcript_data = {
                    "text": transcript_text,
                    "segments": segments,
                    "source_file": smi_path.name,
                    "course_id": course_id,
                    "instructor_id": instructor_id,
                }

                with transcript_file_path.open("w", encoding="utf-8") as f:
                    json.dump(transcript_data, f, ensure_ascii=False, indent=2)

                if transcript_file_path.exists():
                    transcript_path = str(transcript_file_path)
                    print(f"[{course_id}] ✅ SMI transcript JSON saved: {transcript_path}")

                # persona 샘플 + 세그먼트 인제스트
                texts.append(transcript_text)
                print(f"[{course_id}] 📝 {len(segments)}개 자막 세그먼트 인제스트 시작...")
                total_segments = len(segments)
                batch_texts = []
                batch_metas = []
                batch_size = 20
                for idx, seg in enumerate(segments):
                    seg_text = seg.get("text", "")
                    if not seg_text:
                        continue
                    seg_meta = {
                        "course_id": course_id,
                        "instructor_id": instructor_id,
                        "source": smi_path.name,
                        "start_time": seg.get("start"),
                        "end_time": seg.get("end"),
                        "segment_index": idx,
                        "start_formatted": seg.get("start_formatted"),
                        "end_formatted": seg.get("end_formatted"),
                        "type": "subtitle_segment",
                    }
                    batch_texts.append(seg_text)
                    batch_metas.append(seg_meta)
                    
                    # 진행률 업데이트 (30% ~ 60%)
                    if update_progress and total_segments > 0:
                        embedding_progress = 30 + int((idx + 1) / total_segments * 30)
                        update_progress(embedding_progress, f"세그먼트 임베딩 중... ({idx + 1}/{total_segments})")

                    # 배치 인제스트
                    is_last = idx == total_segments - 1
                    if batch_texts and (len(batch_texts) >= batch_size or is_last):
                        try:
                            result = pipeline.ingest_texts_with_metadatas(
                                batch_texts,
                                course_id=course_id,
                                metadatas=batch_metas,
                            )
                            ingested_count += result.get("ingested", 0)
                        except Exception as batch_error:
                            print(f"[{course_id}] ⚠️ SMI 세그먼트 배치 인제스트 오류: {batch_error}")
                            for retry_text, retry_meta in zip(batch_texts, batch_metas):
                                try:
                                    result = pipeline.ingest_texts(
                                        [retry_text],
                                        course_id=course_id,
                                        metadata=retry_meta,
                                    )
                                    ingested_count += result.get("ingested", 0)
                                except Exception as seg_error:
                                    print(f"[{course_id}] ⚠️ SMI 세그먼트 인제스트 재시도 오류: {seg_error}")
                                    continue
                        finally:
                            batch_texts = []
                            batch_metas = []
                print(f"[{course_id}] ✅ 자막 세그먼트 인제스트 완료")
                if update_progress:
                    update_progress(60, "세그먼트 임베딩 완료")
                    
            except Exception as e:
                error_msg = f"[{course_id}] ❌ SMI 처리 오류 ({smi_path.name if smi_path else 'unknown'}): {str(e)}"
                print(error_msg)
                # 오류가 발생해도 계속 진행
        # SMI가 없으면 기존 STT 처리
        elif media_path and media_path.exists():
            try:
                if update_progress:
                    update_progress(15, "파일 준비 중...")
                print(f"[{course_id}] 🎤 STT 처리 시작: {media_path.name}")

                # 첫 업로드이므로 무조건 STT 실행
                if update_progress:
                    update_progress(20, "음성 인식(STT) 시작...")
                # 기존 transcript가 있으면 해시 비교 후 재사용
                transcript_path = None
                force_retranscribe = True
                try:
                    from core.config import AppSettings
                    app_settings = AppSettings()
                    course_dir = app_settings.uploads_dir / instructor_id / course_id
                    transcript_filename = f"transcript_{media_path.stem}.json"
                    transcript_file_path = course_dir / transcript_filename

                    if transcript_file_path.exists():
                        # 파일 해시 계산
                        file_hash = hashlib.md5(media_path.read_bytes()).hexdigest()
                        with transcript_file_path.open("r", encoding="utf-8") as f:
                            data = json.load(f)
                        saved_hash = data.get("source_hash")
                        if saved_hash and saved_hash == file_hash:
                            transcript_path = str(transcript_file_path)
                            force_retranscribe = False
                            print(f"[{course_id}] ✅ 기존 transcript 재사용 (해시 일치): {transcript_path}")
                        else:
                            print(f"[{course_id}] ⚠️ transcript 해시 불일치 또는 없음, STT 재실행")
                except Exception as e:
                    print(f"[{course_id}] ⚠️ transcript 재사용 체크 실패, STT 재실행: {e}")

                print(f"[{course_id}] 🔄 Running STT (force_retranscribe={force_retranscribe})...")
                transcript_result = transcribe_video(
                    str(media_path),
                    settings=settings,
                    instructor_id=instructor_id,
                    course_id=course_id,
                    transcript_path=transcript_path,
                    force_retranscribe=force_retranscribe
                )
                transcript_text = transcript_result.get("text", "")
                segments = transcript_result.get("segments", [])
                
                if update_progress:
                    update_progress(40, "음성 인식(STT) 완료, 세그먼트 임베딩 준비 중...")

                print(f"[{course_id}] 📝 STT result - text length: {len(transcript_text)}, segments: {len(segments)}")

                # STT placeholder 체크
                if "placeholder" in transcript_text.lower():
                    error_msg = f"[{course_id}] ❌ STT가 placeholder를 반환했습니다. 실제 전사가 실패했습니다."
                    print(error_msg)
                    raise ValueError(error_msg)

                if not transcript_text or not transcript_text.strip():
                    error_msg = f"[{course_id}] ❌ STT 결과가 비어있습니다."
                    print(error_msg)
                    raise ValueError(error_msg)

                print(f"[{course_id}] ✅ STT 성공! 전사된 텍스트 길이: {len(transcript_text)} 문자")

                # STT 결과를 파일로 저장
                if transcript_text:
                    try:
                        from core.config import AppSettings
                        import json

                        app_settings = AppSettings()
                        course_dir = app_settings.uploads_dir / instructor_id / course_id
                        course_dir.mkdir(parents=True, exist_ok=True)

                        # transcript 파일명: transcript_{원본파일명}.json
                        transcript_filename = f"transcript_{media_path.stem}.json"
                        transcript_file_path = course_dir / transcript_filename

                        # JSON 형식으로 저장 (전체 텍스트 + 세그먼트 정보)
                        transcript_data = {
                            "text": transcript_text,
                            "segments": segments,
                            "source_file": media_path.name,
                            "course_id": course_id,
                            "instructor_id": instructor_id,
                            "source_hash": hashlib.md5(media_path.read_bytes()).hexdigest(),
                        }

                        print(f"[{course_id}] Attempting to save transcript to: {transcript_file_path}")
                        print(f"[{course_id}] Transcript text length: {len(transcript_text)}")

                        with transcript_file_path.open("w", encoding="utf-8") as f:
                            json.dump(transcript_data, f, ensure_ascii=False, indent=2)

                        # 파일이 실제로 저장되었는지 확인
                        if transcript_file_path.exists():
                            file_size = transcript_file_path.stat().st_size
                            transcript_path = str(transcript_file_path)
                            print(f"[{course_id}] ✅ STT transcript JSON saved successfully: {transcript_path} (size: {file_size} bytes)")
                        else:
                            print(f"[{course_id}] ❌ Transcript file was not created: {transcript_file_path}")
                    except Exception as e:
                        import traceback
                        print(f"[{course_id}] ❌ Failed to save transcript file: {e}")
                        print(f"[{course_id}] Error details: {traceback.format_exc()}")
                        # 파일 저장 실패해도 계속 진행

                if transcript_text:
                    # 병합 텍스트 전체를 persona 생성용 샘플에 추가
                    texts.append(transcript_text)

                    # 세그먼트별 메타데이터 포함하여 RAG 인제스트
                    print(f"[{course_id}] 📝 {len(segments)}개 세그먼트 인제스트 시작...")
                    total_segments = len(segments)
                    batch_texts = []
                    batch_metas = []
                    batch_size = 20
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

                        batch_texts.append(seg_text)
                        batch_metas.append(seg_meta)
                        
                        # 진행률 업데이트 (40% ~ 70%)
                        if update_progress and total_segments > 0:
                            embedding_progress = 40 + int((idx + 1) / total_segments * 30)
                            update_progress(embedding_progress, f"세그먼트 임베딩 중... ({idx + 1}/{total_segments})")

                        # 배치 인제스트
                        is_last = idx == total_segments - 1
                        if batch_texts and (len(batch_texts) >= batch_size or is_last):
                            try:
                                result = pipeline.ingest_texts_with_metadatas(
                                    batch_texts,
                                    course_id=course_id,
                                    metadatas=batch_metas,
                                )
                                ingested_count += result.get("ingested", 0)
                            except Exception as batch_error:
                                print(f"[{course_id}] ⚠️ 세그먼트 배치 인제스트 오류: {batch_error}")
                                for retry_text, retry_meta in zip(batch_texts, batch_metas):
                                    try:
                                        result = pipeline.ingest_texts(
                                            [retry_text],
                                            course_id=course_id,
                                            metadata=retry_meta,
                                        )
                                        ingested_count += result.get("ingested", 0)
                                    except Exception as seg_error:
                                        print(f"[{course_id}] ⚠️ 세그먼트 인제스트 재시도 오류: {seg_error}")
                                        continue
                            finally:
                                batch_texts = []
                                batch_metas = []

                    print(f"[{course_id}] ✅ 세그먼트 인제스트 완료")
                    if update_progress:
                        update_progress(70, "세그먼트 임베딩 완료")
                else:
                    print(f"[{course_id}] ⚠️ STT 결과 텍스트가 비어있습니다: {media_path.name}")

            except Exception as e:
                error_msg = f"[{course_id}] ❌ STT 처리 오류 ({media_path.name}): {str(e)}"
                print(error_msg)
                # 오류가 발생해도 계속 진행
        
        # 2. PDF 멀티모달 처리 (텍스트 + 이미지 설명)
        if pdf_path and pdf_path.exists():
            try:
                if update_progress:
                    update_progress(70, "PDF 처리 시작...")
                print(f"[{course_id}] 📄 PDF 멀티모달 처리 시작: {pdf_path.name}")
                print(f"[{course_id}] 📄 이미지 추출 활성화: extract_images=True")
                # PDF 처리 모듈이 있으면 사용, 없으면 스킵
                try:
                    from ai.services.pdf import extract_pdf_content
                    pdf_result = extract_pdf_content(str(pdf_path), settings=settings, extract_images=True)
                    pdf_texts = pdf_result.get("texts", [])
                    pdf_metadata_list = pdf_result.get("metadata", [])
                    print(f"[{course_id}] 📄 PDF 처리 완료: {len(pdf_texts)}개 페이지 추출됨")
                    
                    if pdf_texts:
                        # PDF 텍스트를 persona 생성용 샘플에 추가
                        texts.extend(pdf_texts)
                        
                        # 페이지별로 개별 RAG 인제스트 (페이지 번호 등 메타데이터 포함)
                        print(f"[{course_id}] 🖼️ PDF {len(pdf_texts)}개 페이지 인제스트 시작...")
                        total_pages = len(pdf_texts)
                        batch_texts = []
                        batch_metas = []
                        batch_size = 10
                        for page_idx, (pdf_text, pdf_meta) in enumerate(zip(pdf_texts, pdf_metadata_list)):
                            try:
                                page_num = pdf_meta.get("page_number")
                                if page_num is None:
                                    # pdf_meta에 page_number가 없으면 page_idx + 1 사용
                                    page_num = page_idx + 1
                                    print(f"[{course_id}] ⚠️ PDF 메타데이터에 page_number가 없어서 {page_num}로 설정")

                                page_meta = {
                                    "course_id": course_id,
                                    "instructor_id": instructor_id,
                                    "source": pdf_path.name,
                                    "page_number": page_num,  # 명시적으로 int로 저장
                                    "type": "pdf_page",
                                }
                                print(f"[{course_id}] 📄 PDF 페이지 {page_num} 인제스트: {pdf_text[:50]}...")

                                batch_texts.append(pdf_text)
                                batch_metas.append(page_meta)
                                
                                # 진행률 업데이트 (70% ~ 75%)
                                if update_progress and total_pages > 0:
                                    pdf_progress = 70 + int((page_idx + 1) / total_pages * 5)
                                    update_progress(pdf_progress, f"PDF 페이지 처리 중... ({page_idx + 1}/{total_pages})")
                                
                                # 배치 처리
                                is_last = page_idx == total_pages - 1
                                if batch_texts and (len(batch_texts) >= batch_size or is_last):
                                    try:
                                        print(f"[{course_id}] 📤 PDF 배치 인제스트 시작: {len(batch_texts)}개 페이지 (course_id={course_id})")
                                        for bm in batch_metas:
                                            print(f"[{course_id}] 📄 배치 메타데이터: page_number={bm.get('page_number')} (type: {type(bm.get('page_number')).__name__}), type={bm.get('type')}, course_id={bm.get('course_id')}")
                                        result = pipeline.ingest_texts_with_metadatas(
                                            batch_texts,
                                            course_id=course_id,
                                            metadatas=batch_metas,
                                        )
                                        ingested_count += result.get("ingested", 0)
                                        print(f"[{course_id}] ✅ PDF 배치 인제스트 성공: {result.get('ingested', 0)}개 저장됨")
                                    except Exception as batch_error:
                                        print(f"[{course_id}] ⚠️ PDF 배치 인제스트 오류: {batch_error}")
                                        import traceback
                                        print(f"[{course_id}] 배치 오류 상세: {traceback.format_exc()}")
                                        # 배치 실패 시 페이지 단위로 재시도
                                        for retry_text, retry_meta in zip(batch_texts, batch_metas):
                                            try:
                                                print(f"[{course_id}] 🔄 PDF 페이지 재시도: page_number={retry_meta.get('page_number')}")
                                                result = pipeline.ingest_texts(
                                                    [retry_text],
                                                    course_id=course_id,
                                                    metadata=retry_meta,
                                                )
                                                ingested_count += result.get("ingested", 0)
                                                print(f"[{course_id}] ✅ PDF 페이지 재시도 성공: {result.get('ingested', 0)}개 저장됨")
                                            except Exception as retry_error:
                                                print(f"[{course_id}] ⚠️ PDF 페이지 인제스트 재시도 오류: {retry_error}")
                                                import traceback
                                                print(f"[{course_id}] 재시도 오류 상세: {traceback.format_exc()}")
                                                continue
                                    finally:
                                        batch_texts = []
                                        batch_metas = []
                            except Exception as page_error:
                                print(f"[{course_id}] ⚠️ PDF 페이지 {page_idx + 1} 인제스트 오류: {page_error}")
                                # 개별 페이지 오류는 건너뛰고 계속 진행
                                continue
                        
                        print(f"[{course_id}] ✅ PDF 페이지 인제스트 완료 ({len(pdf_texts)}개 페이지)")
                    else:
                        print(f"[{course_id}] ⚠️ PDF에서 텍스트를 추출하지 못했습니다: {pdf_path.name}")
                        # PDF 텍스트가 없어도 계속 진행
                except ImportError:
                    print(f"[{course_id}] ⚠️ PDF 처리 모듈이 없습니다. PDF 처리를 건너뜁니다.")
                    # PDF 처리 모듈이 없어도 계속 진행
                except Exception as pdf_error:
                    # PDF 처리 중 치명적 오류 발생 시에도 계속 진행
                    error_msg = f"[{course_id}] ⚠️ PDF 처리 중 오류 발생: {str(pdf_error)}"
                    print(error_msg)
                    import traceback
                    print(f"[{course_id}] PDF 오류 상세: {traceback.format_exc()}")
                    # PDF 처리는 실패했지만 나머지 처리 계속 진행
                        
            except Exception as e:
                error_msg = f"[{course_id}] ❌ PDF 처리 오류 ({pdf_path.name}): {str(e)}"
                print(error_msg)
                # 오류가 발생해도 계속 진행
        
        # 3. Style Analyzer 실행 (강의 목록 단위 말투 관리)
        # - 부모 강의(parent_course_id가 null)에 persona_profile 저장
        # - 챕터(parent_course_id가 있음)는 부모 강의의 persona_profile 재사용
        persona_profile_json = None
        if segments and len(segments) > 0:
            if update_progress:
                update_progress(75, "강사 스타일 분석 중...")
            
            # 현재 course가 챕터인지 부모 강의인지 확인
            parent_course_id = None
            is_chapter = False
            try:
                from core.db import engine
                from sqlmodel import Session
                from core.models import Course
                
                with Session(engine) as db_session:
                    current_course = db_session.get(Course, course_id)
                    if current_course:
                        parent_course_id = current_course.parent_course_id
                        is_chapter = parent_course_id is not None
                        if is_chapter:
                            print(f"[{course_id}] 📚 챕터 감지됨 (부모 강의: {parent_course_id})")
                        else:
                            print(f"[{course_id}] 📖 부모 강의 감지됨")
            except Exception as db_e:
                print(f"[{course_id}] ⚠️ Course 정보 확인 실패: {db_e}")
                # DB 조회 실패해도 계속 진행
            
            # 챕터인 경우: 부모 강의의 persona_profile 재사용
            if is_chapter and parent_course_id:
                try:
                    from core.db import engine
                    from sqlmodel import Session
                    from core.models import Course
                    
                    with Session(engine) as db_session:
                        parent_course = db_session.get(Course, parent_course_id)
                        if parent_course and parent_course.persona_profile:
                            persona_profile_json = parent_course.persona_profile
                            print(f"[{course_id}] ✅ 부모 강의 말투 발견 (재사용): {parent_course_id}")
                            print(f"[{course_id}] ♻️ 부모 강의 말투 재사용 (API 호출 생략)")
                        else:
                            print(f"[{course_id}] ⚠️ 부모 강의({parent_course_id})의 말투가 없습니다. 새로 분석합니다.")
                            # 부모 강의 말투가 없으면 새로 분석 (부모 강의에 저장)
                            is_chapter = False  # 부모 강의처럼 처리
                            parent_course_id = None
                except Exception as db_e:
                    print(f"[{course_id}] ⚠️ 부모 강의 말투 확인 실패: {db_e}")
                    # 부모 강의 말투 확인 실패 시 새로 분석
                    is_chapter = False
                    parent_course_id = None
            
            # 부모 강의인 경우 (또는 부모 강의 말투가 없는 챕터): 부모 강의의 persona_profile 확인
            if not is_chapter:
                target_course_id = course_id  # 부모 강의 ID 사용
                try:
                    from core.db import engine
                    from sqlmodel import Session
                    from core.models import Course
                    
                    with Session(engine) as db_session:
                        target_course = db_session.get(Course, target_course_id)
                        if target_course and target_course.persona_profile:
                            # 부모 강의 말투가 이미 있으면 재사용
                            persona_profile_json = target_course.persona_profile
                            print(f"[{course_id}] ✅ 부모 강의 말투 발견 (재사용): {target_course_id}")
                            print(f"[{course_id}] ♻️ 부모 강의 말투 재사용 (API 호출 생략)")
                        else:
                            # 부모 강의 말투가 없으면 새로 분석
                            print(f"[{course_id}] 🧑‍🏫 Style Analyzer 실행 (초반 10~20분 분석)...")
                            try:
                                persona_profile = analyze_instructor_style(segments, settings=settings)
                                persona_profile_json = json.dumps(persona_profile, ensure_ascii=False)
                                print(f"[{course_id}] ✅ Style Analyzer 완료: {persona_profile_json[:100]}...")
                                
                                # 부모 강의의 persona_profile에 저장
                                try:
                                    with Session(engine) as db_session:
                                        target_course = db_session.get(Course, target_course_id)
                                        if target_course:
                                            target_course.persona_profile = persona_profile_json
                                            db_session.add(target_course)
                                            db_session.commit()
                                            db_session.refresh(target_course)
                                            print(f"[{course_id}] ✅ 부모 강의 말투를 Course DB에 저장 완료 (course_id: {target_course_id})")
                                        else:
                                            print(f"[{course_id}] ⚠️ 부모 강의({target_course_id})를 찾을 수 없어 말투를 저장하지 못했습니다.")
                                except Exception as db_e:
                                    print(f"[{course_id}] ⚠️ 부모 강의 말투 DB 저장 실패: {db_e}")
                                    # DB 저장 실패해도 계속 진행
                                
                            except Exception as e:
                                error_msg = f"[{course_id}] ❌ Style Analyzer 오류: {str(e)}"
                                print(error_msg)
                                # Style Analyzer 실패해도 계속 진행
                except Exception as db_e:
                    print(f"[{course_id}] ⚠️ 부모 강의 말투 확인 실패: {db_e}")
                    # DB 조회 실패해도 계속 진행
        
        # 4. 페르소나 프롬프트 생성 및 RAG 인제스트
        if texts:
            if update_progress:
                update_progress(80, "페르소나 프롬프트 생성 중...")
            print(f"[{course_id}] 🧑‍🏫 페르소나 프롬프트 생성 시작...")
            # Style Analyzer 결과가 있으면 사용, 없으면 기존 방식 사용
            try:
                if persona_profile_json:
                    # Style Analyzer 결과를 사용하여 페르소나 프롬프트 생성
                    from ai.style_analyzer import create_persona_prompt
                    persona_dict = json.loads(persona_profile_json)
                    persona_prompt = create_persona_prompt(persona_dict)
                    # ⚠️ 강사 정보는 ChromaDB에 저장하지 않음 (DB에서 동적으로 로드)
                    # instructor_info는 분석 시에만 참고하고, 페르소나 프롬프트에는 포함하지 않음
                else:
                    # 기존 방식 (fallback) - 강사 정보는 포함하지 않음 (DB에서 동적으로 로드)
                    persona_prompt = pipeline.generate_persona_prompt(
                        course_id=course_id,
                        sample_texts=texts,
                        instructor_info=None  # ChromaDB에 저장하지 않음
                    )
                
                if update_progress:
                    update_progress(85, "페르소나 저장 중...")
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
                print(f"[{course_id}] ✅ 페르소나 프롬프트 저장 완료")
                if update_progress:
                    update_progress(95, "최종 처리 중...")
                
            except Exception as e:
                error_msg = f"[{course_id}] ❌ 페르소나 프롬프트 생성 오류: {str(e)}"
                print(error_msg)
                # 페르소나 추출 실패해도 계속 진행
        else:
            print(f"[{course_id}] ⚠️ 처리할 텍스트가 없습니다.")
        
        return {
            "status": "completed",
            "ingested_count": ingested_count,
            "transcript_path": transcript_path,  # STT 결과 파일 경로 (있는 경우)
            "persona_profile": persona_profile_json,  # Style Analyzer 결과 (JSON 문자열, backB가 DB에 저장)
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
