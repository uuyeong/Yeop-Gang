"""
페르소나 학습 상태 점검 스크립트
- 벡터 DB에 저장된 페르소나 확인
- 페르소나 프롬프트 내용 확인
- 챗봇이 페르소나를 사용하는지 테스트

사용법:
  cd server
  python check_persona.py [course_id]
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "server"))

from ai.config import AISettings
from ai.services.vectorstore import get_chroma_client, get_collection
from ai.pipelines.rag import RAGPipeline


def check_persona_in_db(course_id: str):
    """벡터 DB에서 페르소나 확인"""
    settings = AISettings()
    client = get_chroma_client(settings)
    collection = get_collection(client, settings)
    
    print(f"\n{'='*70}")
    print(f"페르소나 학습 상태 점검: {course_id}")
    print(f"{'='*70}\n")
    
    # 모든 데이터 조회
    all_data = collection.get()
    
    # course_id와 type="persona"로 필터링
    persona_docs = []
    for i, doc_id in enumerate(all_data.get('ids', [])):
        metadata = all_data.get('metadatas', [{}])[i] if all_data.get('metadatas') else {}
        if metadata.get('course_id') == course_id and metadata.get('type') == 'persona':
            doc_text = all_data.get('documents', [''])[i] if all_data.get('documents') else ''
            persona_docs.append({
                'id': doc_id,
                'metadata': metadata,
                'text': doc_text,
            })
    
    if persona_docs:
        print(f"✅ 페르소나가 벡터 DB에 저장되어 있습니다!\n")
        for idx, persona in enumerate(persona_docs, 1):
            print(f"[{idx}] 페르소나 ID: {persona['id']}")
            print(f"    메타데이터: {persona['metadata']}")
            print(f"    페르소나 프롬프트 (처음 500자):")
            print(f"    {persona['text'][:500]}...")
            if len(persona['text']) > 500:
                print(f"    ... (전체 {len(persona['text'])}자)")
            print()
    else:
        print(f"❌ 페르소나가 벡터 DB에 저장되어 있지 않습니다.")
        print(f"   파일을 업로드하고 처리해야 페르소나가 생성됩니다.\n")
    
    # 해당 course_id의 전체 문서 수 확인
    course_docs = []
    for i, doc_id in enumerate(all_data.get('ids', [])):
        metadata = all_data.get('metadatas', [{}])[i] if all_data.get('metadatas') else {}
        if metadata.get('course_id') == course_id:
            course_docs.append(metadata.get('type', 'unknown'))
    
    print(f"📊 {course_id}의 전체 문서 수: {len(course_docs)}")
    if course_docs:
        from collections import Counter
        type_counts = Counter(course_docs)
        print(f"   문서 타입별 분포:")
        for doc_type, count in type_counts.items():
            print(f"   - {doc_type}: {count}개")
    print()


def test_persona_usage(course_id: str, test_question: str = "안녕하세요, 간단히 자기소개 해주세요."):
    """페르소나가 실제로 사용되는지 테스트"""
    settings = AISettings()
    pipeline = RAGPipeline(settings)
    
    print(f"\n{'='*70}")
    print(f"페르소나 사용 테스트: {course_id}")
    print(f"{'='*70}\n")
    print(f"테스트 질문: {test_question}\n")
    
    # 쿼리 실행
    result = pipeline.query(
        question=test_question,
        course_id=course_id,
        k=5,
    )
    
    # 페르소나가 검색되었는지 확인
    persona_found = False
    for meta in result.get('metadatas', []):
        if meta.get('type') == 'persona':
            persona_found = True
            print(f"✅ 페르소나가 검색되었습니다!")
            print(f"   메타데이터: {meta}\n")
            break
    
    if not persona_found:
        print(f"⚠️ 페르소나가 검색 결과에 포함되지 않았습니다.")
        print(f"   (페르소나가 없거나 검색되지 않았을 수 있습니다)\n")
    
    # 답변 확인
    answer = result.get('answer', '')
    print(f"챗봇 답변:")
    print(f"{answer}\n")
    
    # 답변에서 말투 특징 확인 (간단한 휴리스틱)
    print(f"말투 특징 분석:")
    if any(word in answer for word in ['습니다', '습니다.', '습니다!']):
        print(f"   - 정중한 종결어미 사용 (습니다)")
    if any(word in answer for word in ['어요', '어요.', '어요!']):
        print(f"   - 친근한 종결어미 사용 (어요)")
    if any(word in answer for word in ['죠', '죠.', '죠!']):
        print(f"   - 친근한 종결어미 사용 (죠)")
    if any(word in answer for word in ['네요', '네요.', '네요!']):
        print(f"   - 친근한 종결어미 사용 (네요)")
    
    print()


if __name__ == "__main__":
    course_id = sys.argv[1] if len(sys.argv) > 1 else "test-course-1"
    
    # 1. 벡터 DB에서 페르소나 확인
    check_persona_in_db(course_id)
    
    # 2. 페르소나 사용 테스트
    test_persona_usage(course_id)
    
    print(f"{'='*70}")
    print("점검 완료!")
    print(f"{'='*70}\n")

