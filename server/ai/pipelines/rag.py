from typing import Iterable, Optional, List, Dict, Any
from chromadb.errors import InvalidDimensionException

from ai.config import AISettings
from ai.services.vectorstore import get_chroma_client, get_collection
from ai.services.embeddings import embed_texts

try:
    from openai import OpenAI
    from openai import RateLimitError, APIError
except Exception:
    OpenAI = None  # type: ignore
    RateLimitError = None  # type: ignore
    APIError = None  # type: ignore


class RAGPipeline:
    """
    Minimal RAG pipeline scaffold.
    Backend A can extend methods to add embeddings, retrievers, and LLM calls.
    """

    def __init__(self, settings: AISettings):
        self.settings = settings
        self.client = get_chroma_client(settings)
        self.collection = get_collection(self.client, settings)

    def _recreate_collection_on_dimension_mismatch(self, e: InvalidDimensionException) -> None:
        """Recreates the collection if a dimension mismatch occurs."""
        print(f"Warning: {e}. Attempting to recreate collection '{self.collection.name}'...")
        self.client.delete_collection(name=self.collection.name)
        self.collection = get_collection(self.client, self.settings)
        print(f"Collection '{self.collection.name}' recreated. Please re-ingest data.")

    def ingest_texts(
        self,
        texts: Iterable[str],
        *,
        course_id: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Ingest texts with embeddings and course-scoped metadata.
        
        IDs are generated to be unique:
        - If metadata has segment_index: use "{course_id}-seg-{segment_index}"
        - If metadata has page_number: use "{course_id}-page-{page_number}"
        - Otherwise: use "{course_id}-doc-{i}" with auto-increment
        """
        entries = list(texts)
        if not entries:
            return {"ingested": 0}

        md = metadata or {}
        md.setdefault("course_id", course_id)

        embeddings = embed_texts(entries, self.settings)

        # Generate unique IDs based on metadata
        ids = []
        metadatas = []
        
        for i, entry in enumerate(entries):
            current_metadata = {**md, "course_id": course_id} # Ensure course_id is always present
            
            # Use segment_index or page_number if available for unique ID
            if current_metadata.get("segment_index") is not None:
                doc_id = f"{course_id}-seg-{current_metadata['segment_index']}"
            elif current_metadata.get("page_number") is not None:
                doc_id = f"{course_id}-page-{current_metadata['page_number']}"
            elif current_metadata.get("type") == "persona":
                doc_id = f"{course_id}-persona"
            else:
                # Fallback: use index (may cause overwrites if called multiple times without unique metadata)
                doc_id = f"{course_id}-doc-{i}"
            
            ids.append(doc_id)
            metadatas.append(current_metadata)

        try:
            self.collection.upsert(
                ids=ids,
                documents=entries,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        except InvalidDimensionException as e:
            self._recreate_collection_on_dimension_mismatch(e)
            return {"ingested": 0, "error": "Collection recreated due to dimension mismatch. Please re-ingest."}
        except (RateLimitError, APIError) as e:
            error_msg = f"OpenAI API 오류 (임베딩): {str(e)}"
            print(f"ERROR [Ingest]: {error_msg}")
            return {"ingested": 0, "error": error_msg}

        return {"ingested": len(entries)}

    def query(
        self, 
        question: str, 
        *, 
        course_id: str, 
        k: int = 4,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        current_time: Optional[float] = None
    ) -> dict:
        """
        Retrieval with course_id filter + LLM synthesis.
        Supports conversation history for context-aware responses.
        
        Args:
            question: Current question
            course_id: Course identifier
            k: Number of documents to retrieve
            conversation_history: List of previous messages in format [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        try:
            # 질문을 임베딩으로 변환 (ingest_texts와 동일한 방식)
            try:
                query_embeddings = embed_texts([question], self.settings)
            except ValueError as e:
                # API 할당량 초과 등 임베딩 생성 실패 시
                error_msg = str(e)
                if "할당량" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                    detailed_msg = (
                        "⚠️ OpenAI API 할당량이 초과되었습니다.\n\n"
                        "해결 방법:\n"
                        "1. OpenAI 대시보드(https://platform.openai.com/account/billing)에서 크레딧 잔액 확인\n"
                        "2. 결제 정보 등록 및 크레딧 추가\n"
                        "3. Rate Limits(https://platform.openai.com/account/limits) 확인\n\n"
                        f"에러 상세: {error_msg}"
                    )
                else:
                    detailed_msg = f"⚠️ 임베딩 생성 중 오류가 발생했습니다: {error_msg}"
                
                return {
                    "question": question,
                    "documents": [],
                    "metadatas": [],
                    "answer": detailed_msg,
                }
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=k + 1,  # 페르소나 프롬프트 포함을 위해 +1
                include=["documents", "metadatas", "distances"],
                where={"course_id": course_id},
            )
        except ValueError as e:
            # API 키나 할당량 관련 에러
            error_msg = str(e)
            return {
                "question": question,
                "documents": [],
                "metadatas": [],
                "answer": f"⚠️ {error_msg}",
            }
        except Exception as exc:
            # If collection dimension mismatch occurs (old collection), recreate and return placeholder
            if isinstance(exc, InvalidDimensionException):
                # Recreate collection with current embedding model name suffix
                self.collection = get_collection(self.client, self.settings)
                return {
                    "question": question,
                    "documents": [],
                    "metadatas": [],
                    "answer": "벡터 컬렉션을 재생성했습니다. 다시 질문해주세요.",
                }
            raise
        docs_all = results.get("documents", []) or [[]]
        metas_all = results.get("metadatas", []) or [[]]
        distances_all = results.get("distances", []) or [[]]
        docs: List[str] = docs_all[0] if docs_all else []
        metas: List[Dict[str, Any]] = metas_all[0] if metas_all else []
        distances: List[float] = distances_all[0] if distances_all else []
        
        # 디버깅: 검색 결과 로그
        print(f"[RAG DEBUG] Query: '{question[:50]}...' (course_id={course_id})")
        print(f"[RAG DEBUG] Found {len(docs)} documents")
        if docs:
            for i, (doc, meta, dist) in enumerate(zip(docs[:3], metas[:3], distances[:3])):
                source = meta.get("source", "unknown")
                start_time = meta.get("start_time")
                print(f"[RAG DEBUG] Doc {i+1}: {doc[:100]}... (source={source}, time={start_time}s, distance={dist:.4f})")
        else:
            print(f"[RAG DEBUG] ⚠️ No documents found for course_id={course_id}")
            # 벡터 DB에 데이터가 있는지 확인
            try:
                all_docs = self.collection.get(
                    where={"course_id": course_id},
                    limit=1
                )
                if not all_docs.get("ids") or len(all_docs["ids"]) == 0:
                    print(f"[RAG DEBUG] ❌ No documents in vector DB for course_id={course_id}. Course may not be processed yet.")
                else:
                    print(f"[RAG DEBUG] ✅ Vector DB has documents for course_id={course_id}, but search returned nothing. This may indicate an embedding mismatch.")
            except Exception as e:
                print(f"[RAG DEBUG] ⚠️ Could not check vector DB: {e}")
        
        # 페르소나를 명시적으로 별도 검색 (질문과 관계없이 항상 가져오기)
        # ⚠️ query_texts를 사용하면 ChromaDB가 내부적으로 임베딩을 생성할 수 있으므로
        # get() 메서드만 사용하여 불필요한 API 호출 방지
        persona_doc = None
        try:
            # ID로 직접 가져오기 (임베딩 생성 없음)
            persona_results = self.collection.get(
                ids=[f"{course_id}-persona"],
                include=["documents", "metadatas"],
            )
            if persona_results.get("documents") and len(persona_results["documents"]) > 0:
                persona_doc = persona_results["documents"][0]
                print(f"[RAG DEBUG] ✅ 페르소나를 ID로 검색했습니다 (course_id={course_id}, 임베딩 호출 없음)")
            else:
                print(f"[RAG DEBUG] ⚠️ 페르소나가 벡터 DB에 없습니다 (course_id={course_id})")
        except Exception as e:
            # get()이 실패하면 (예: ID가 없거나 컬렉션 문제) 페르소나 없이 진행
            print(f"[RAG DEBUG] ⚠️ 페르소나 검색 중 오류 (get 실패): {e}")
            # ⚠️ query_texts를 사용하지 않음 - 불필요한 임베딩 API 호출 방지
        
        # 검색 결과에서 페르소나 제거 및 시간 기반 필터링/정렬
        filtered_docs = []
        filtered_metas = []
        doc_scores = []  # 시간 기반 점수 (가까울수록 높은 점수)
        
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            if meta.get("type") != "persona":
                # 시간 기반 점수 계산 (current_time이 있는 경우)
                score = 0.0
                if current_time is not None and current_time > 0:
                    start_time = meta.get("start_time")
                    end_time = meta.get("end_time")
                    if start_time is not None or end_time is not None:
                        # 현재 시간과의 거리 계산
                        if start_time is not None and end_time is not None:
                            # segment 범위 내에 있으면 높은 점수
                            if start_time <= current_time <= end_time:
                                score = 100.0
                            else:
                                # 거리에 따라 점수 감소
                                mid_time = (start_time + end_time) / 2
                                distance = abs(mid_time - current_time)
                                score = max(0, 100.0 - distance / 10)  # 10초당 10점 감소
                        elif start_time is not None:
                            distance = abs(start_time - current_time)
                            score = max(0, 100.0 - distance / 10)
                        elif end_time is not None:
                            distance = abs(end_time - current_time)
                            score = max(0, 100.0 - distance / 10)
                
                filtered_docs.append(doc)
                filtered_metas.append(meta)
                doc_scores.append(score)
        
        # 시간 기반 점수가 있으면 정렬 (높은 점수부터)
        if current_time is not None and current_time > 0 and any(s > 0 for s in doc_scores):
            # 점수와 거리를 함께 고려하여 정렬
            sorted_items = sorted(
                zip(filtered_docs, filtered_metas, doc_scores),
                key=lambda x: (x[2], -x[1].get("start_time", 0) if x[1].get("start_time") else 0),
                reverse=True
            )
            filtered_docs = [doc for doc, _, _ in sorted_items]
            filtered_metas = [meta for _, meta, _ in sorted_items]
            print(f"[RAG DEBUG] 📍 Time-based sorting applied (current_time={current_time}s), top score: {max(doc_scores) if doc_scores else 0:.1f}")
        
        answer = self._llm_answer(
            question, 
            filtered_docs, 
            filtered_metas, 
            course_id,
            conversation_history=conversation_history,
            persona_doc=persona_doc  # 명시적으로 페르소나 전달
        )
        return {
            "question": question,
            "documents": docs,
            "metadatas": metas,
            "answer": answer,
        }

    def _llm_answer(
        self, 
        question: str, 
        docs: List[str], 
        metas: List[Dict[str, Any]], 
        course_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        persona_doc: Optional[str] = None
    ) -> str:
        """
        LLM synthesis with persona prompt and conversation history.
        Audio knowledge takes priority, GPT knowledge is supplementary.
        """
        if OpenAI is None or not self.settings.openai_api_key:
            return "LLM placeholder: OPENAI_API_KEY가 없어서 기본 답변을 반환합니다."

        context_parts = []
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            src = meta.get("source") or meta.get("filename") or ""
            ts = meta.get("start_time")
            ctx = f"[{src} @ {ts}s] {doc}" if ts is not None else doc
            context_parts.append(ctx)
        context = "\n".join(context_parts) if context_parts else ""

        # 저장된 페르소나 프롬프트 사용 (있으면), 없으면 검색된 문서로 생성
        if persona_doc:
            persona = persona_doc
            print(f"[RAG DEBUG] ✅ 저장된 페르소나 프롬프트 사용 (course_id={course_id})")
        else:
            # 페르소나 프롬프트를 찾지 못한 경우, 검색된 문서로 생성 (fallback)
            print(f"[RAG DEBUG] ⚠️ 저장된 페르소나를 찾지 못해 검색된 문서로 생성 (fallback, course_id={course_id})")
            persona = self.generate_persona_prompt(course_id=course_id, sample_texts=docs)
        
        # 오디오 지식 우선, GPT 지식 보조 프롬프트
        if context:
            knowledge_instruction = (
                "중요: 아래 '강의 컨텍스트'에 있는 내용이 가장 우선순위가 높습니다. "
                "먼저 강의 컨텍스트에서 답을 찾으세요. "
                "강의 컨텍스트에 명확한 답이 있으면 그대로 사용하세요. "
                "강의 컨텍스트에 없는 내용이 필요할 때만 일반적인 지식으로 보완하세요.\n\n"
                "강의 컨텍스트:\n"
                f"{context}\n\n"
                "위 강의 컨텍스트를 바탕으로 질문에 답변하세요. "
                "강의 내용을 직접 인용하거나 요약하여 답변하세요."
            )
        else:
            knowledge_instruction = (
                "⚠️ 경고: 강의 컨텍스트를 찾지 못했습니다. "
                "이는 강의가 아직 처리되지 않았거나, 벡터 DB에 데이터가 없을 수 있습니다. "
                "일반적인 지식으로 답변하되, 강의 범위와 관련된 내용임을 명시하세요. "
                "강의 내용을 확인할 수 없으므로 정확한 답변을 제공하기 어렵습니다."
            )
            print(f"[RAG DEBUG] ⚠️ No context found for course_id={course_id}, question: {question[:50]}")
            # 컨텍스트가 없으면 명시적으로 표시 (상위 레벨에서 transcript 파일 사용하도록)
            answer = knowledge_instruction
            return {
                "question": question,
                "documents": [],
                "metadatas": [],
                "answer": answer,
            }
        
        sys_prompt = (
            f"{persona}\n\n"
            "위 말투 지시사항을 정확히 따라 답변하세요.\n\n"
            f"{knowledge_instruction}\n\n"
            "답변 규칙:\n"
            "- 강의 컨텍스트의 내용을 최우선으로 사용하세요.\n"
            "- 강의 컨텍스트에 없는 내용은 일반 지식으로 보완 가능하지만, 강의 내용임을 강조하세요.\n"
            "- 모르면 모른다고 말하세요.\n"
            "- 코스 범위 밖 질문은 답하지 않습니다.\n"
            "- 이전 대화 내용도 참고하여 일관성 있게 답변하세요."
        )

        # 메시지 구성 (대화 히스토리 포함)
        messages = [{"role": "system", "content": sys_prompt}]
        
        # 대화 히스토리 추가 (최근 10개만 유지)
        if conversation_history:
            # 최근 10개 메시지만 포함 (토큰 제한 고려)
            recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ["user", "assistant"] and content:
                    messages.append({"role": role, "content": content})
        
        # 현재 질문 추가
        messages.append({"role": "user", "content": question})

        client = OpenAI(api_key=self.settings.openai_api_key)
        try:
            resp = client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                temperature=0.3,
            )
            return resp.choices[0].message.content
        except RateLimitError as e:
            error_msg = f"OpenAI API 할당량이 초과되었습니다: {str(e)}"
            print(f"ERROR [LLM]: {error_msg}")
            return f"⚠️ {error_msg}"
        except APIError as e:
            error_msg = f"OpenAI API 오류가 발생했습니다: {str(e)}"
            print(f"ERROR [LLM]: {error_msg}")
            return f"⚠️ {error_msg}"
        except Exception as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg or "quota" in error_msg.lower():
                return "⚠️ OpenAI API 할당량이 초과되었습니다. OpenAI 계정의 크레딧을 확인하거나 결제 정보를 업데이트하세요."
            elif "rate_limit" in error_msg.lower() or "429" in error_msg:
                return "⚠️ OpenAI API Rate Limit 초과: 잠시 후 다시 시도하세요."
            else:
                return f"⚠️ LLM 응답 생성 중 오류 발생: {error_msg}"

    def generate_persona_prompt(
        self, *, course_id: str, sample_texts: list[str]
    ) -> str:
        """
        Analyze speaking style from sample texts and generate persona prompt.
        Uses LLM to extract stylistic patterns (speech patterns, tone, expressions).
        """
        if not sample_texts:
            return f"당신은 course_id={course_id} 강사의 말투를 모방한 AI입니다."
        
        if OpenAI is None or not self.settings.openai_api_key:
            # Fallback to simple prompt if API key is missing
            sample = sample_texts[0][:500] if sample_texts else ""
            return (
                f"당신은 course_id={course_id} 강사의 말투를 모방한 AI입니다. "
                f"아래 샘플을 참고하여 답변하세요:\n{sample}"
            )
        
        # Combine sample texts (up to 3000 chars to avoid token limits)
        combined_text = "\n\n".join(sample_texts)
        if len(combined_text) > 3000:
            combined_text = combined_text[:3000] + "..."
        
        # Use LLM to analyze speaking style
        client = OpenAI(api_key=self.settings.openai_api_key)
        
        analysis_prompt = f"""다음은 강사의 강의 텍스트 샘플입니다. 이 강사의 말투와 스타일을 분석해주세요.

분석할 요소:
1. 종결어미 패턴 (예: "-습니다", "-어요", "-죠", "-네요" 등)
2. 어투 (정중함, 친근함, 격식, 캐주얼 등)
3. 자주 사용하는 표현이나 습관적 말투
4. 문장 구조 (짧은 문장 vs 긴 문장)
5. 특징적인 말버릇이나 반복되는 표현

강의 샘플:
{combined_text}

분석 결과를 다음 형식으로 작성해주세요:
- 종결어미: [분석 결과]
- 어투: [분석 결과]
- 자주 사용하는 표현: [분석 결과]
- 문장 구조: [분석 결과]
- 특징: [분석 결과]

이 분석을 바탕으로 이 강사의 말투를 모방하는 방법을 요약해주세요."""
        
        try:
            resp = client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 언어학자이자 스타일 분석 전문가입니다. 주어진 텍스트에서 말투와 스타일을 정확하게 분석합니다.",
                    },
                    {"role": "user", "content": analysis_prompt},
                ],
                temperature=0.3,
            )
            style_analysis = resp.choices[0].message.content
            
            # Generate persona prompt based on analysis
            persona_instruction = f"""당신은 course_id={course_id} 강사의 말투와 스타일을 정확하게 모방하는 AI 챗봇입니다.

강사 말투 분석:
{style_analysis}

위 분석을 바탕으로 다음 규칙을 지켜 답변하세요:
1. 분석된 종결어미 패턴을 정확히 사용하세요
2. 분석된 어투를 일관되게 유지하세요
3. 자주 사용하는 표현이나 특징적인 말버릇을 자연스럽게 사용하세요
4. 문장 구조도 원본과 유사하게 작성하세요
5. 강사의 개성과 특징을 반영하여 친근하고 자연스러운 말투로 답변하세요"""
            
            return persona_instruction
        except (RateLimitError, APIError) as e:
            error_msg = f"OpenAI API 오류 (페르소나 생성): {str(e)}"
            print(f"ERROR [Persona]: {error_msg}")
            sample = sample_texts[0][:500] if sample_texts else ""
            return (
                f"당신은 course_id={course_id} 강사의 말투를 모방한 AI입니다. "
                f"페르소나 생성 중 오류가 발생했습니다: {error_msg}. "
                f"아래 샘플을 참고하여 답변하세요:\n{sample}"
            )
        except Exception as e:
            print(f"Warning: Failed to analyze persona style: {e}")
            # Fallback to simple prompt
            sample = sample_texts[0][:500] if sample_texts else ""
            return (
                f"당신은 course_id={course_id} 강사의 말투를 모방한 AI입니다. "
                f"아래 샘플을 참고하여 답변하세요:\n{sample}"
            )

