"""
입시 정보 크롤링 데이터 로더 및 처리
수만휘 게시판 크롤링 데이터를 로드하고 벡터 DB에 저장
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# 프로젝트 루트 경로 (server/ai/services/admission_data.py -> 프로젝트 루트)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CRAWLING_DIR = PROJECT_ROOT / "ref" / "크롤링"


def load_admission_csv_files() -> List[Dict[str, Any]]:
    """
    크롤링 폴더의 CSV 파일들을 로드하여 입시 정보 리스트로 반환
    
    Returns:
        입시 정보 딕셔너리 리스트
        각 딕셔너리는 {"title": 제목, "content": 본문, "comments": 댓글, "source": 출처} 형식
    """
    admission_data = []
    
    if not CRAWLING_DIR.exists():
        logger.warning(f"크롤링 폴더가 존재하지 않습니다: {CRAWLING_DIR}")
        return admission_data
    
    # 처리할 CSV 파일 목록
    csv_files = [
        "파인튜닝용.csv",
        "N수게시판.csv",
        "서성한게시판.csv",
        "연고대게시판.csv",
        "이과정시.csv",
        "중경외시이게시판.csv",
    ]
    
    for csv_file in csv_files:
        csv_path = CRAWLING_DIR / csv_file
        if not csv_path.exists():
            logger.warning(f"CSV 파일이 존재하지 않습니다: {csv_path}")
            continue
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # CSV 컬럼명에 따라 데이터 추출
                    title = row.get('제목', row.get('title', ''))
                    content = row.get('본문', row.get('content', row.get('본문', '')))
                    comments = row.get('댓글데이터', row.get('comments', row.get('댓글', '')))
                    
                    # 빈 데이터는 스킵
                    if not title and not content:
                        continue
                    
                    # 본문과 댓글을 합쳐서 하나의 텍스트로 구성
                    full_text = f"제목: {title}\n\n본문: {content}"
                    if comments and comments != "댓글없음" and comments.strip():
                        full_text += f"\n\n댓글: {comments}"
                    
                    admission_data.append({
                        "title": title,
                        "content": content,
                        "comments": comments,
                        "full_text": full_text,
                        "source": csv_file.replace('.csv', ''),
                    })
            
            logger.info(f"✅ {csv_file} 로드 완료: {len([d for d in admission_data if d['source'] == csv_file.replace('.csv', '')])}개 항목")
        
        except Exception as e:
            logger.error(f"❌ {csv_file} 로드 중 오류: {e}")
            continue
    
    logger.info(f"📊 총 {len(admission_data)}개의 입시 정보 항목 로드 완료")
    return admission_data


def prepare_admission_texts_for_ingestion(admission_data: List[Dict[str, Any]]) -> List[str]:
    """
    입시 정보 데이터를 벡터 DB 저장용 텍스트 리스트로 변환
    
    Args:
        admission_data: load_admission_csv_files()로 로드한 데이터
        
    Returns:
        벡터 DB에 저장할 텍스트 리스트
    """
    texts = []
    
    for item in admission_data:
        # full_text를 그대로 사용 (제목 + 본문 + 댓글)
        texts.append(item["full_text"])
    
    return texts


def prepare_admission_metadatas_for_ingestion(admission_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    입시 정보 데이터를 벡터 DB 저장용 메타데이터 리스트로 변환
    
    Args:
        admission_data: load_admission_csv_files()로 로드한 데이터
        
    Returns:
        벡터 DB에 저장할 메타데이터 리스트
    """
    metadatas = []
    
    for i, item in enumerate(admission_data):
        metadata = {
            "type": "admission_info",
            "source": item["source"],
            "title": item["title"][:200] if item["title"] else "",  # 제목은 최대 200자
            "index": i,
        }
        metadatas.append(metadata)
    
    return metadatas


def load_and_prepare_admission_data() -> tuple[List[str], List[Dict[str, Any]]]:
    """
    입시 정보를 로드하고 벡터 DB 저장용으로 준비
    
    Returns:
        (texts, metadatas) 튜플
    """
    admission_data = load_admission_csv_files()
    texts = prepare_admission_texts_for_ingestion(admission_data)
    metadatas = prepare_admission_metadatas_for_ingestion(admission_data)
    
    return texts, metadatas

