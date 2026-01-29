# 옆강 (Yeop-Gang) 아키텍처 문서

이 문서는 옆강 프로젝트의 상세한 시스템 아키텍처를 설명합니다.

## 📋 목차

- [시스템 아키텍처 개요](#시스템-아키텍처-개요)
- [데이터 흐름](#데이터-흐름)
- [RAG 파이프라인](#rag-파이프라인)
- [페르소나 추출 시스템](#페르소나-추출-시스템)
- [멀티모달 처리](#멀티모달-처리)
- [강의명/회차 구분 시스템](#강의명회차-구분-시스템)
- [보안 및 가드레일](#보안-및-가드레일)
- [성능 최적화](#성능-최적화)
- [데이터베이스 설계](#데이터베이스-설계)
- [배포 아키텍처](#배포-아키텍처)

## 시스템 아키텍처 개요

### 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  강사 UI     │  │  학생 UI     │  │  공통 컴포넌트│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Layer (Backend B)                                │  │
│  │  - 인증/인가 (JWT)                                    │  │
│  │  - Rate Limiting                                      │  │
│  │  - Guardrails                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AI Layer (Backend A)                                 │  │
│  │  - RAG Pipeline                                       │  │
│  │  - STT (Whisper)                                      │  │
│  │  - Style Analyzer                                    │  │
│  │  - Multimodal Processing                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  SQLite      │  │  ChromaDB    │  │  File Storage│
│  (메타데이터) │  │  (벡터 DB)   │  │  (업로드 파일)│
└──────────────┘  └──────────────┘  └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌──────────────┐
                    │  OpenAI API  │
                    │  - GPT-4o    │
                    │  - Whisper   │
                    │  - Embeddings│
                    │  - VLM       │
                    └──────────────┘
```

### 레이어별 역할

#### 1. Frontend Layer (Next.js)
- **역할**: 사용자 인터페이스 및 상호작용
- **주요 기능**:
  - 강사/학생 이원화 UI
  - 비디오 플레이어 + 챗봇 통합 인터페이스
  - 타임라인 점프 기능
  - 요약노트 및 퀴즈 표시
  - API 프록시 (통합 배포 시 백엔드로 요청 전달)

#### 2. API Layer (Backend B)
- **역할**: 요청 처리, 인증, 권한 관리, 보안
- **주요 기능**:
  - JWT 기반 인증/인가
  - Rate Limiting (시간당 100회)
  - Guardrails (프롬프트 인젝션 방어)
  - 파일 업로드 관리
  - Background Task 오케스트레이션

#### 3. AI Layer (Backend A)
- **역할**: AI 기능 구현 및 파이프라인 관리
- **주요 기능**:
  - STT (Speech-to-Text)
  - 페르소나 추출 (Style Analyzer, 강의 목록 단위)
  - RAG 파이프라인 (검색 + 생성)
  - 멀티모달 처리 (PDF 이미지/도표)

#### 4. Data Layer
- **SQLite**: 메타데이터, 사용자 정보, 강의 정보
- **ChromaDB**: 벡터 임베딩 저장 및 유사도 검색
- **File Storage**: 업로드된 비디오, 오디오, PDF 파일

## 데이터 흐름

### 1. 강의 업로드 플로우

```
[프론트엔드] POST /api/instructor/upload
    │
    ▼
[Backend B] 파일 저장 + Background Task 트리거
    │
    ▼
[Backend B] process_course_assets() 호출
    │
    ├─→ [Backend A] transcribe_video() → STT (Whisper API)
    │       │
    │       └─→ transcript.json 저장
    │
    ├─→ [Backend A] parse_smi_file() → SMI 자막 파싱 (있는 경우)
    │       │
    │       └─→ SMI 우선 사용, 없으면 STT 결과 사용
    │
    ├─→ [Backend A] extract_pdf_content() → PDF 처리
    │       │
    │       ├─→ 텍스트 추출 (페이지별)
    │       └─→ 이미지/도표 추출 → VLM 설명 생성
    │
    ├─→ [Backend A] analyze_instructor_style() → 페르소나 추출
    │       │
    │       └─→ 초반 10~20분 스크립트 분석
    │           └─→ JSON: {tone, philosophy, signature_keywords}
    │           └─→ 부모 강의의 persona_profile에 저장 (챕터는 재사용)
    │
    └─→ [Backend A] pipeline.ingest_texts() → 벡터 DB 저장
            │
            ├─→ STT/SMI 세그먼트 → ChromaDB
            ├─→ PDF 페이지 → ChromaDB
            └─→ 페르소나 프롬프트 → ChromaDB
    │
    ▼
[Backend B] Course.status = "completed"
    │
    ▼
[프론트엔드] 상태 폴링으로 완료 확인
```

### 2. 챗봇 질의응답 플로우

```
[프론트엔드] POST /api/chat/ask
    │
    ▼
[Backend B] Guardrails 검증
    │
    ├─→ 프롬프트 인젝션 방어
    ├─→ 부적절한 질문 필터링
    └─→ 컨텍스트 외 질문 감지
    │
    ▼
[Backend B] _get_course_and_instructor_info() → DB에서 정보 로드
    │
    ├─→ 강사 정보 (이름, 소개, 전문 분야)
    ├─→ 강의 정보 (제목, 카테고리)
    └─→ 페르소나 프로필 (JSON)
    │
    ▼
[Backend A] pipeline.query() → RAG 파이프라인
    │
    ├─→ 질문 타입 분석 (일반 질문 vs PDF 특정 질문)
    │
    ├─→ 페이지 번호 추출 (있는 경우)
    │
    ├─→ 벡터 검색 (ChromaDB)
    │   │
    │   ├─→ 페이지 번호가 있으면 직접 검색 (collection.get())
    │   └─→ 없으면 유사도 검색 (collection.query())
    │
    ├─→ 강의명/회차 정보 로드 (부모 강의명, 챕터 번호)
    │
    ├─→ 컨텍스트 구성
    │   │
    │       ├─→ 검색된 문서들 (강의 컨텍스트)
    │   ├─→ 페르소나 프롬프트 (부모 강의에서 로드)
    │   ├─→ 강사/강의 정보 (DB에서 동적 로드)
    │   ├─→ 강의명/회차 정보 (부모 강의명, 챕터 번호)
    │   └─→ 시스템 프롬프트 (보안 규칙, Grounding 규칙, 반복 표현 지양)
    │
    └─→ LLM 호출 (GPT-4o)
        │
        └─→ 답변 생성 + 타임스탬프 포함
    │
    ▼
[Backend B] 맞춤법 검사 (py-hanspell)
    │
    ▼
[프론트엔드] 답변 표시 + 타임라인 이동
```

## RAG 파이프라인

### 구조

```
┌─────────────────────────────────────────────────────────┐
│                    RAG Pipeline                          │
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │  Ingest      │      │  Query       │                │
│  │  (저장)      │      │  (검색+생성) │                │
│  └──────────────┘      └──────────────┘                │
│         │                     │                         │
│         ▼                     ▼                         │
│  ┌──────────────┐      ┌──────────────┐                │
│  │  Embedding   │      │  Retrieval    │                │
│  │  (임베딩)    │      │  (벡터 검색)  │                │
│  └──────────────┘      └──────────────┘                │
│         │                     │                         │
│         ▼                     ▼                         │
│  ┌──────────────┐      ┌──────────────┐                │
│  │  ChromaDB    │      │  LLM (GPT-4o) │                │
│  │  (저장)      │      │  (생성)       │                │
│  └──────────────┘      └──────────────┘                │
└─────────────────────────────────────────────────────────┘
```

### Ingest (저장) 프로세스

1. **텍스트 입력**: STT 세그먼트, PDF 페이지, 페르소나 프롬프트
2. **임베딩 생성**: OpenAI `text-embedding-3-small` 모델 사용
3. **메타데이터 구성**:
   - `course_id`: 강의 식별자
   - `instructor_id`: 강사 식별자
   - `segment_index`: STT 세그먼트 인덱스 (있는 경우)
   - `page_number`: PDF 페이지 번호 (있는 경우)
   - `type`: 문서 타입 (transcript, pdf, persona)
4. **ChromaDB 저장**: 벡터 + 메타데이터 저장

### Query (검색+생성) 프로세스

1. **질문 분석**:
   - 페이지 번호 추출 (정규표현식)
   - 질문 타입 판단 (일반 질문 vs PDF 특정 질문)
2. **벡터 검색**:
   - 페이지 번호가 있으면: `collection.get()` 직접 검색
   - 없으면: `collection.query()` 유사도 검색 (k=5~20)
   - 결과 필터링 및 우선순위 정렬
3. **컨텍스트 구성**:
   - 검색된 문서들 (최대 5개)
   - 페르소나 프롬프트
   - 강사/강의 정보
   - 시스템 프롬프트
4. **LLM 호출**: GPT-4o로 답변 생성
5. **후처리**: 맞춤법 검사, 수학 공식 렌더링

### 하이브리드 검색 전략

- **직접 검색**: 페이지 번호가 명시된 경우 `collection.get()` 사용
- **벡터 검색**: 일반 질문의 경우 유사도 기반 검색
- **필터링**: 검색 결과에서 페이지 번호 매칭 문서 우선순위 상향

## 페르소나 추출 시스템

### Style Analyzer 알고리즘

```
┌─────────────────────────────────────────────────────────┐
│              Style Analyzer Pipeline                     │
│                                                          │
│  1. STT/SMI 세그먼트 입력                                │
│     │                                                    │
│     ▼                                                    │
│  2. 초반 10~20분 분량 추출                              │
│     │                                                    │
│     ▼                                                    │
│  3. LLM 분석 (GPT-4o)                                   │
│     │                                                    │
│     ├─→ tone (말투)                                     │
│     ├─→ philosophy (교육 철학)                          │
│     └─→ signature_keywords (자주 쓰는 말)              │
│     │                                                    │
│     ▼                                                    │
│  4. JSON 출력                                           │
│     {                                                   │
│       "tone": "친근하고 격려하는",                      │
│       "philosophy": "이해 중심 학습",                    │
│       "signature_keywords": ["이해가 잘 안 가는", ...]  │
│     }                                                   │
│     │                                                    │
│     ▼                                                    │
│  5. 페르소나 프롬프트 생성                               │
│     │                                                    │
│     ▼                                                    │
│  6. ChromaDB 저장                                       │
└─────────────────────────────────────────────────────────┘
```

### 하이브리드 페르소나 관리

- **부모 강의 기반**: 같은 강의 목록(부모 강의) 내의 모든 챕터는 동일한 페르소나 공유
- **재사용 전략**: 
  - 챕터 업로드 시 부모 강의의 `persona_profile` 확인
  - 있으면 재사용 (API 호출 생략)
  - 없으면 새로 분석 후 부모 강의에 저장
- **분석 시간**: 초반 10~20분 분량의 스크립트를 분석하여 더 정확한 페르소나 추출

### 페르소나 적용 범위

- **챗봇 답변**: 모든 답변에 페르소나 적용
- **인사말**: 초기 인사말도 페르소나 기반 생성
- **오류 메시지**: 거절 메시지, 오류 메시지도 페르소나 적용
- **반복 표현 지양**: 동일한 문구("질문해 주세요" 등)를 반복하지 않고 다양한 표현 사용
- **요약/퀴즈**: 과목 특성 반영 (페르소나와 별개)

## 멀티모달 처리

### PDF 처리 파이프라인

```
┌─────────────────────────────────────────────────────────┐
│              PDF Processing Pipeline                     │
│                                                          │
│  1. PDF 파일 입력                                        │
│     │                                                    │
│     ▼                                                    │
│  2. 페이지별 처리 (PyMuPDF)                              │
│     │                                                    │
│     ├─→ 텍스트 추출                                      │
│     │   └─→ 페이지 번호 메타데이터 포함                 │
│     │                                                    │
│     └─→ 이미지/도표 추출                                │
│         │                                                │
│         ├─→ 이미지 감지 (PIL)                           │
│         │                                                │
│         └─→ VLM 설명 생성 (GPT-4o Vision)              │
│             └─→ "이미지/도표 설명: ..." 형식으로 저장  │
│     │                                                    │
│     ▼                                                    │
│  3. 벡터 DB 저장                                        │
│     │                                                    │
│     ├─→ 텍스트 → ChromaDB                               │
│     └─→ 이미지 설명 → ChromaDB                          │
└─────────────────────────────────────────────────────────┘
```

### 이미지/도표 처리

- **이미지 감지**: PyMuPDF로 PDF에서 이미지 추출
- **VLM 설명**: GPT-4o Vision API로 이미지 설명 생성
- **저장 형식**: `"이미지/도표 설명: [VLM 설명]"` 형식으로 텍스트와 함께 저장
- **검색**: 텍스트 검색과 동일하게 벡터 검색으로 접근 가능

### 페이지 번호 기반 검색

- **메타데이터**: 각 PDF 페이지에 `page_number` 메타데이터 저장
- **직접 검색**: 사용자가 "4페이지 설명해줘"라고 하면 `collection.get()`으로 직접 검색
- **필터링**: 벡터 검색 결과에서 페이지 번호 매칭 문서 우선순위 상향

## 보안 및 가드레일

### Guardrails 시스템

```
┌─────────────────────────────────────────────────────────┐
│              Guardrails Pipeline                         │
│                                                          │
│  1. 사용자 질문 입력                                     │
│     │                                                    │
│     ▼                                                    │
│  2. validate_question()                                  │
│     │                                                    │
│     ├─→ 프롬프트 인젝션 패턴 검사                       │
│     ├─→ 금지 키워드 필터링                              │
│     └─→ 컨텍스트 외 질문 감지                           │
│     │                                                    │
│     ▼                                                    │
│  3. sanitize_question()                                  │
│     │                                                    │
│     └─→ 민감한 부분 제거                                │
│     │                                                    │
│     ▼                                                    │
│  4. 시스템 프롬프트에 보안 규칙 추가                    │
│     │                                                    │
│     ├─→ 시스템 역할 변경 금지                           │
│     ├─→ 컨텍스트 외 질문 처리                           │
│     ├─→ 부적절한 질문 처리                              │
│     └─→ 강의 컨텍스트 고수                              │
│     │                                                    │
│     ▼                                                    │
│  5. LLM 호출                                            │
│     │                                                    │
│     └─→ 안전한 답변 생성                                │
└─────────────────────────────────────────────────────────┘
```

### 보안 규칙

1. **프롬프트 인젝션 방어**:
   - "프롬프트를 잊어라", "역할을 변경해라" 등의 패턴 차단
   - 시스템 역할 변경 시도 차단

2. **부적절한 질문 필터링**:
   - 욕설, 위협 표현 차단
   - 금지 키워드 목록 기반 필터링

3. **컨텍스트 외 질문 처리**:
   - 강의와 완전히 무관한 질문 차단
   - 단, 강의 내용과 관련된 수능 질문은 허용

4. **페르소나 적용 거절 메시지**:
   - 모든 거절 메시지도 강사 말투로 생성

### Rate Limiting

- **제한**: 시간당 100회 요청
- **헤더**: `X-RateLimit-*` 헤더로 상태 전달
- **예외**: `/api/health`, `/api/status/*` 등은 제한 제외

## 성능 최적화

### 캐싱 전략

#### 1. 인사말 캐시
- **TTL**: 300초 (5분)
- **키**: `course_id`
- **효과**: 동일 강의의 인사말 재사용 시 API 호출 생략

#### 2. 요약/퀴즈 캐시
- **TTL**: 300초 (5분)
- **키**: `(course_id, format)` 또는 `(course_id, num_questions)`
- **효과**: 동일 강의의 요약/퀴즈 재생성 시 API 호출 생략

#### 3. Transcript 캐시
- **TTL**: 120초 (2분)
- **키**: `(course_id, include_timestamps)`
- **효과**: 요약/퀴즈 생성 시 transcript 로드 속도 개선

#### 4. 임베딩 캐시
- **방식**: ChromaDB 내장 캐싱
- **효과**: 동일 텍스트의 재임베딩 방지

#### 5. VLM 이미지 설명 캐시
- **TTL**: 무제한 (파일 해시 기반)
- **키**: 이미지 파일 해시
- **효과**: 동일 이미지의 재설명 생성 방지

#### 6. 요약/퀴즈 생성 최적화
- **전사 텍스트 길이 제한**: 요약노트 15,000자, 퀴즈 12,000자로 제한
- **응답 길이 제한**: 요약노트 `max_tokens=3000`, 퀴즈 `max_tokens=2000`
- **효과**: 긴 전사 텍스트 처리 시간 단축, 응답 생성 속도 개선

### 배치 처리

#### 1. PDF 페이지 배치 임베딩
- **방식**: 여러 페이지를 한 번에 임베딩
- **효과**: API 호출 횟수 감소, 처리 속도 개선

#### 2. STT 세그먼트 배치 임베딩
- **방식**: 여러 세그먼트를 한 번에 임베딩
- **효과**: API 호출 횟수 감소, 처리 속도 개선

### 파일 해시 기반 재사용

- **STT 결과 재사용**: 동일 파일(해시)의 STT 결과 재사용
- **효과**: 동일 파일 재업로드 시 STT API 호출 생략

## 데이터베이스 설계

### SQLite 스키마

#### Instructor 테이블
```sql
CREATE TABLE instructor (
    id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    password_hash TEXT,
    bio TEXT,
    specialization TEXT,
    profile_image_url TEXT,
    persona_profile TEXT,  -- JSON 문자열 (기본 페르소나)
    created_at TIMESTAMP
);
```

#### Course 테이블
```sql
CREATE TABLE course (
    id TEXT PRIMARY KEY,
    instructor_id TEXT,
    title TEXT,
    category TEXT,  -- 과목 (필수, 예: "영어", "수학")
    status TEXT,  -- processing, completed, failed
    progress INTEGER,  -- 0-100
    persona_profile TEXT,  -- JSON 문자열 (부모 강의 페르소나)
    parent_course_id TEXT,  -- 챕터인 경우 부모 강의 ID
    chapter_number INTEGER,  -- 챕터 번호 (1, 2, 3...)
    total_chapters INTEGER,  -- 전체 강의 수 (부모 강의에만 사용)
    is_public BOOLEAN,  -- 학생에게 공개 여부
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (instructor_id) REFERENCES instructor(id),
    FOREIGN KEY (parent_course_id) REFERENCES course(id)
);
```

#### Video 테이블
```sql
CREATE TABLE video (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id TEXT,
    file_path TEXT,
    file_type TEXT,  -- video, audio, pdf, smi
    created_at TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES course(id)
);
```

#### Student 테이블
```sql
CREATE TABLE student (
    id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    password_hash TEXT,
    created_at TIMESTAMP
);
```

#### CourseEnrollment 테이블
```sql
CREATE TABLE courseenrollment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    course_id TEXT,
    status TEXT,  -- active, completed
    enrolled_at TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(id),
    FOREIGN KEY (course_id) REFERENCES course(id)
);
```

### ChromaDB 스키마

#### Collection 구조

##### 1. 강의 컨텍스트 컬렉션 (`yeopgang-embeddings`)
- **이름**: `yeopgang-embeddings` (또는 설정값)
- **임베딩 차원**: 1536 (text-embedding-3-small)
- **메타데이터 필드**:
  - `course_id`: 강의 식별자 (필수)
  - `instructor_id`: 강사 식별자
  - `segment_index`: STT 세그먼트 인덱스
  - `page_number`: PDF 페이지 번호 (정수)
  - `type`: 문서 타입 (subtitle_segment, video_segment, audio_segment, pdf_page, persona)
  - `start_time`: 세그먼트 시작 시간 (초)
  - `end_time`: 세그먼트 종료 시간 (초)
  - `source`: 원본 파일명

#### 문서 ID 형식
- STT 세그먼트: `{course_id}-seg-{segment_index}`
- PDF 페이지: `{course_id}-page-{page_number}`
- 페르소나: `{course_id}-persona`
- 기타: `{course_id}-doc-{i}-{timestamp}` (타임스탬프 포함으로 중복 방지)

### 데이터 격리 (Multi-tenancy)

- **course_id 기반 격리**: 모든 벡터 검색은 `course_id` 메타데이터로 필터링
- **권한 기반 접근**: 강사는 자신의 강의만, 학생은 등록한 강의만 접근 가능

## 결론

옆강 프로젝트는 다음과 같은 특징을 가진 AI 기반 학습 플랫폼입니다:

1. **페르소나 기반 학습**: 각 강사의 고유한 말투와 교육 철학을 자동으로 학습
2. **멀티모달 통합**: 비디오, 오디오, PDF, 자막을 통합하여 완벽한 컨텍스트 제공
3. **실시간 상호작용**: 타임라인 점프, 실시간 질의응답
4. **과목 특화 기능**: 수학, 영어, 과학 등 과목별 특성 반영
5. **보안 및 안정성**: Guardrails, Rate Limiting, 인증/인가
6. **성능 최적화**: 캐싱, 배치 처리, 파일 해시 기반 재사용

이러한 아키텍처를 통해 사용자에게 자연스럽고 안전한 학습 경험을 제공합니다.

