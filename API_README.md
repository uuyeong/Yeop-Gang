# 옆강 (Yeop-Gang) API 사용 가이드

백엔드 B에서 제공하는 REST API 사용법을 설명하는 문서입니다.

## 📋 목차

- [기본 정보](#기본-정보)
- [인증](#인증)
- [강사용 API](#강사용-api)
- [학생용 API](#학생용-api)
- [공통 API](#공통-api)
- [에러 처리](#에러-처리)
- [예시 코드](#예시-코드)

---

## 기본 정보

### 서버 주소

- **개발 환경**: `http://localhost:8000`
- **API 기본 경로**: `http://localhost:8000/api`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 인증 방식

대부분의 API는 JWT(JSON Web Token) 기반 인증을 사용합니다.

**인증 헤더 형식:**

```
Authorization: Bearer <access_token>
```

### Rate Limiting

- **제한**: 시간당 100회 요청
- **헤더**: 응답에 `X-RateLimit-*` 헤더 포함
- **제외 경로**: `/api/health`, `/api/status/*` 등은 제한 제외

---

## 인증

### 1. 강사 등록

강사 계정을 생성하고 JWT 토큰을 받습니다.

**엔드포인트:** `POST /api/auth/register/instructor`

**요청 본문:**

```json
{
  "id": "instructor-1",
  "name": "홍길동",
  "email": "hong@example.com",
  "password": "password123"
}
```

**응답:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "instructor-1",
  "role": "instructor",
  "expires_in": 86400
}
```

**cURL 예시:**

```bash
curl -X POST "http://localhost:8000/api/auth/register/instructor" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "instructor-1",
    "name": "홍길동",
    "email": "hong@example.com",
    "password": "password123"
  }'
```

### 2. 학생 등록

학생 계정을 생성하고 JWT 토큰을 받습니다.

**엔드포인트:** `POST /api/auth/register/student`

**요청 본문:**

```json
{
  "id": "student-1",
  "name": "김철수",
  "email": "kim@example.com",
  "password": "password123"
}
```

**응답:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "student-1",
  "role": "student",
  "expires_in": 86400
}
```

### 3. 로그인

기존 계정으로 로그인하여 JWT 토큰을 받습니다.

**엔드포인트:** `POST /api/auth/login`

**요청 본문:**

```json
{
  "user_id": "instructor-1",
  "password": "password123",
  "role": "instructor"
}
```

**응답:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "instructor-1",
  "role": "instructor",
  "expires_in": 86400
}
```

---

## 강사용 API

### 1. 강의 업로드

비디오/오디오/PDF 파일을 업로드하고 백그라운드 처리를 시작합니다.

**엔드포인트:** `POST /api/instructor/upload`

**인증:** 강사 토큰 필요

**요청 형식:** `multipart/form-data`

**파라미터:**

- `instructor_id` (필수): 강사 ID
- `course_id` (필수): 강의 ID
- `video` (선택): 비디오 파일 (mp4, avi, mov, mkv, webm)
- `audio` (선택): 오디오 파일 (mp3, wav, m4a, aac, ogg, flac)
- `pdf` (선택): PDF 파일

**응답:**

```json
{
  "course_id": "course-1",
  "instructor_id": "instructor-1",
  "status": "processing"
}
```

**cURL 예시:**

```bash
curl -X POST "http://localhost:8000/api/instructor/upload" \
  -H "Authorization: Bearer <instructor_token>" \
  -F "instructor_id=instructor-1" \
  -F "course_id=course-1" \
  -F "video=@/path/to/video.mp4"
```

**Python 예시:**

```python
import requests

url = "http://localhost:8000/api/instructor/upload"
headers = {"Authorization": f"Bearer {instructor_token}"}
files = {
    "video": open("video.mp4", "rb"),
    "audio": open("audio.mp3", "rb"),  # 선택사항
}
data = {
    "instructor_id": "instructor-1",
    "course_id": "course-1"
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### 2. 강의 목록 조회

강사가 업로드한 모든 강의 목록을 조회합니다.

**엔드포인트:** `GET /api/instructor/courses`

**인증:** 강사 토큰 필요

**응답:**

```json
[
  {
    "id": "course-1",
    "title": "Python 기초",
    "status": "completed",
    "created_at": "2024-01-01T00:00:00"
  },
  {
    "id": "course-2",
    "title": "JavaScript 고급",
    "status": "processing",
    "created_at": "2024-01-02T00:00:00"
  }
]
```

**cURL 예시:**

```bash
curl -X GET "http://localhost:8000/api/instructor/courses" \
  -H "Authorization: Bearer <instructor_token>"
```

---

## 학생용 API

### 1. 강의 등록

학생이 강의에 등록합니다.

**엔드포인트:** `POST /api/student/enroll`

**인증:** 학생 토큰 필요

**요청 본문:**

```json
{
  "course_id": "course-1"
}
```

**응답:**

```json
{
  "enrollment_id": 1,
  "student_id": "student-1",
  "course_id": "course-1",
  "status": "active",
  "enrolled_at": "2024-01-01T00:00:00"
}
```

**cURL 예시:**

```bash
curl -X POST "http://localhost:8000/api/student/enroll" \
  -H "Authorization: Bearer <student_token>" \
  -H "Content-Type: application/json" \
  -d '{"course_id": "course-1"}'
```

### 2. 등록한 강의 목록 조회

학생이 등록한 강의 목록을 조회합니다.

**엔드포인트:** `GET /api/student/courses`

**인증:** 학생 토큰 필요

**응답:**

```json
[
  {
    "id": "course-1",
    "title": "Python 기초",
    "status": "completed",
    "enrolled_at": "2024-01-01T00:00:00"
  }
]
```

**cURL 예시:**

```bash
curl -X GET "http://localhost:8000/api/student/courses" \
  -H "Authorization: Bearer <student_token>"
```

---

## 공통 API

### 1. 헬스체크

서버 상태를 확인합니다.

**엔드포인트:** `GET /api/health`

**인증:** 불필요

**응답:**

```json
{
  "status": "ok",
  "service": "Yeop-Gang"
}
```

**cURL 예시:**

```bash
curl -X GET "http://localhost:8000/api/health"
```

### 2. 처리 상태 조회

강의 처리 상태와 진행률을 조회합니다.

**엔드포인트:** `GET /api/status/{course_id}`

**인증:** 강사 또는 학생 토큰 필요 (강의 접근 권한 필요)

**응답:**

```json
{
  "course_id": "course-1",
  "status": "processing",
  "progress": 50,
  "message": null
}
```

**상태 값:**

- `processing`: 처리 중
- `completed`: 처리 완료
- `failed`: 처리 실패
- `not_found`: 강의를 찾을 수 없음

**cURL 예시:**

```bash
curl -X GET "http://localhost:8000/api/status/course-1" \
  -H "Authorization: Bearer <token>"
```

### 3. 비디오/오디오 스트리밍

강의 비디오 또는 오디오 파일을 스트리밍합니다.

**엔드포인트:** `GET /api/video/{course_id}`

**인증:** 강사 또는 학생 토큰 필요 (강의 접근 권한 필요)

**지원 형식:**

- 비디오: mp4, avi, mov, mkv, webm
- 오디오: mp3, wav, m4a, aac, ogg, flac

**특징:**

- HTTP Range 요청 지원 (대용량 파일 최적화)
- 자동으로 비디오 또는 오디오 파일 감지

**cURL 예시:**

```bash
curl -X GET "http://localhost:8000/api/video/course-1" \
  -H "Authorization: Bearer <token>" \
  --output video.mp4
```

**HTML 예시:**

```html
<video controls>
  <source src="http://localhost:8000/api/video/course-1" type="video/mp4" />
</video>
```

### 4. 챗봇 질의

강의 내용에 대한 질문을 하고 AI 답변을 받습니다.

**엔드포인트:** `POST /api/chat/ask`

**인증:** 강사 또는 학생 토큰 필요 (강의 접근 권한 필요)

**요청 본문:**

```json
{
  "course_id": "course-1",
  "question": "Python에서 리스트는 어떻게 사용하나요?",
  "conversation_id": "student-1:course-1"
}
```

**응답:**

```json
{
  "answer": "Python에서 리스트는 다음과 같이 사용할 수 있습니다...",
  "sources": ["course-1-segment-5", "course-1-segment-12"],
  "conversation_id": "student-1:course-1",
  "course_id": "course-1",
  "is_safe": true,
  "filtered": false
}
```

**cURL 예시:**

```bash
curl -X POST "http://localhost:8000/api/chat/ask" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "course-1",
    "question": "Python에서 리스트는 어떻게 사용하나요?",
    "conversation_id": "student-1:course-1"
  }'
```

**Python 예시:**

```python
import requests

url = "http://localhost:8000/api/chat/ask"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
data = {
    "course_id": "course-1",
    "question": "Python에서 리스트는 어떻게 사용하나요?",
    "conversation_id": "student-1:course-1"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
print(result["answer"])
```

### 5. 강의 요약 생성

강의 내용을 요약하고 주요 포인트를 추출합니다.

**엔드포인트:** `POST /api/summary`

**인증:** 강사 또는 학생 토큰 필요 (강의 접근 권한 필요)

**요청 본문:**

```json
{
  "course_id": "course-1"
}
```

**응답:**

```json
{
  "course_id": "course-1",
  "summary": "이 강의는 Python 기초에 대해 다룹니다...",
  "key_points": [
    "리스트와 딕셔너리의 차이점",
    "반복문과 조건문 사용법",
    "함수 정의 및 호출 방법"
  ]
}
```

**cURL 예시:**

```bash
curl -X POST "http://localhost:8000/api/summary" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"course_id": "course-1"}'
```

### 6. 퀴즈 생성

강의 내용을 기반으로 객관식 퀴즈를 생성합니다.

**엔드포인트:** `POST /api/quiz/generate`

**인증:** 강사 또는 학생 토큰 필요 (강의 접근 권한 필요)

**요청 본문:**

```json
{
  "course_id": "course-1",
  "num_questions": 5
}
```

**응답:**

```json
{
  "course_id": "course-1",
  "quiz_id": "quiz-course-1-1234567890",
  "questions": [
    {
      "id": 1,
      "question": "Python에서 리스트를 만드는 방법은?",
      "options": ["list()", "[]", "array()", "둘 다"],
      "correct_answer": 3,
      "explanation": null
    }
  ]
}
```

**cURL 예시:**

```bash
curl -X POST "http://localhost:8000/api/quiz/generate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "course-1",
    "num_questions": 5
  }'
```

### 7. 퀴즈 답변 제출

퀴즈 답변을 제출하고 점수를 받습니다.

**엔드포인트:** `POST /api/quiz/submit`

**인증:** 강사 또는 학생 토큰 필요 (강의 접근 권한 필요)

**요청 본문:**

```json
{
  "course_id": "course-1",
  "quiz_id": "quiz-course-1-1234567890",
  "answers": {
    "1": 3,
    "2": 0,
    "3": 2,
    "4": 1,
    "5": 0
  }
}
```

**응답:**

```json
{
  "course_id": "course-1",
  "score": 4,
  "total": 5,
  "percentage": 80.0,
  "correct_answers": [1, 2, 3, 4],
  "wrong_answers": [5]
}
```

**cURL 예시:**

```bash
curl -X POST "http://localhost:8000/api/quiz/submit" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "course-1",
    "quiz_id": "quiz-course-1-1234567890",
    "answers": {
      "1": 3,
      "2": 0,
      "3": 2,
      "4": 1,
      "5": 0
    }
  }'
```

### 8. 강의 목록 조회 (공개)

모든 강의 목록을 조회합니다 (인증 불필요).

**엔드포인트:** `GET /api/courses`

**인증:** 불필요

**응답:**

```json
[
  {
    "id": "course-1",
    "title": "Python 기초",
    "status": "completed",
    "instructor_id": "instructor-1",
    "created_at": "2024-01-01T00:00:00",
    "progress": 100
  }
]
```

### 9. 강의 삭제

강의를 삭제합니다 (DB, 벡터 DB, 파일 모두 삭제).

**엔드포인트:** `DELETE /api/courses/{course_id}`

**인증:** 불필요 (향후 강사 권한 체크 추가 예정)

**응답:**

```json
{
  "message": "강의 'course-1'가 삭제되었습니다.",
  "course_id": "course-1"
}
```

**cURL 예시:**

```bash
curl -X DELETE "http://localhost:8000/api/courses/course-1"
```

---

## 에러 처리

### HTTP 상태 코드

- `200 OK`: 요청 성공
- `201 Created`: 리소스 생성 성공
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 필요 또는 토큰 만료
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스를 찾을 수 없음
- `429 Too Many Requests`: Rate limit 초과
- `500 Internal Server Error`: 서버 오류

### 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

### 주요 에러 시나리오

#### 1. 인증 실패

**상태 코드:** `401 Unauthorized`

**응답:**

```json
{
  "detail": "Invalid authentication credentials"
}
```

#### 2. 권한 없음

**상태 코드:** `403 Forbidden`

**응답:**

```json
{
  "detail": "Access denied. You are not enrolled in this course."
}
```

#### 3. Rate Limit 초과

**상태 코드:** `429 Too Many Requests`

**응답:**

```json
{
  "detail": "Rate limit exceeded. Try again in 3600 seconds."
}
```

**헤더:**

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1234567890
```

#### 4. 강의를 찾을 수 없음

**상태 코드:** `404 Not Found`

**응답:**

```json
{
  "detail": "Course not found"
}
```

---

## 예시 코드

### Python 전체 워크플로우 예시

```python
import requests
import time

BASE_URL = "http://localhost:8000/api"

# 1. 강사 등록
print("1. 강사 등록 중...")
register_response = requests.post(
    f"{BASE_URL}/auth/register/instructor",
    json={
        "id": "instructor-1",
        "name": "홍길동",
        "email": "hong@example.com",
        "password": "password123"
    }
)
instructor_token = register_response.json()["access_token"]
print(f"강사 토큰: {instructor_token[:50]}...")

# 2. 강의 업로드
print("\n2. 강의 업로드 중...")
with open("video.mp4", "rb") as f:
    upload_response = requests.post(
        f"{BASE_URL}/instructor/upload",
        headers={"Authorization": f"Bearer {instructor_token}"},
        files={"video": f},
        data={
            "instructor_id": "instructor-1",
            "course_id": "course-1"
        }
    )
print(f"업로드 결과: {upload_response.json()}")

# 3. 처리 상태 확인 (폴링)
print("\n3. 처리 상태 확인 중...")
while True:
    status_response = requests.get(
        f"{BASE_URL}/status/course-1",
        headers={"Authorization": f"Bearer {instructor_token}"}
    )
    status = status_response.json()
    print(f"상태: {status['status']}, 진행률: {status['progress']}%")

    if status["status"] == "completed":
        break
    elif status["status"] == "failed":
        print("처리 실패!")
        break

    time.sleep(5)  # 5초마다 확인

# 4. 학생 등록
print("\n4. 학생 등록 중...")
student_response = requests.post(
    f"{BASE_URL}/auth/register/student",
    json={
        "id": "student-1",
        "name": "김철수",
        "email": "kim@example.com",
        "password": "password123"
    }
)
student_token = student_response.json()["access_token"]
print(f"학생 토큰: {student_token[:50]}...")

# 5. 강의 등록
print("\n5. 강의 등록 중...")
enroll_response = requests.post(
    f"{BASE_URL}/student/enroll",
    headers={"Authorization": f"Bearer {student_token}"},
    json={"course_id": "course-1"}
)
print(f"등록 결과: {enroll_response.json()}")

# 6. 챗봇 질의
print("\n6. 챗봇 질의 중...")
chat_response = requests.post(
    f"{BASE_URL}/chat/ask",
    headers={"Authorization": f"Bearer {student_token}"},
    json={
        "course_id": "course-1",
        "question": "이 강의의 핵심 내용은 무엇인가요?",
        "conversation_id": "student-1:course-1"
    }
)
print(f"답변: {chat_response.json()['answer']}")

# 7. 요약 생성
print("\n7. 요약 생성 중...")
summary_response = requests.post(
    f"{BASE_URL}/summary",
    headers={"Authorization": f"Bearer {student_token}"},
    json={"course_id": "course-1"}
)
summary = summary_response.json()
print(f"요약: {summary['summary']}")
print(f"주요 포인트: {summary['key_points']}")

# 8. 퀴즈 생성 및 제출
print("\n8. 퀴즈 생성 중...")
quiz_response = requests.post(
    f"{BASE_URL}/quiz/generate",
    headers={"Authorization": f"Bearer {student_token}"},
    json={"course_id": "course-1", "num_questions": 5}
)
quiz = quiz_response.json()
print(f"퀴즈 ID: {quiz['quiz_id']}")

# 답변 제출 (예시: 모든 문제에 첫 번째 선택지 선택)
answers = {str(q["id"]): 0 for q in quiz["questions"]}
submit_response = requests.post(
    f"{BASE_URL}/quiz/submit",
    headers={"Authorization": f"Bearer {student_token}"},
    json={
        "course_id": "course-1",
        "quiz_id": quiz["quiz_id"],
        "answers": answers
    }
)
result = submit_response.json()
print(f"점수: {result['score']}/{result['total']} ({result['percentage']}%)")
```

### JavaScript/TypeScript 예시

```typescript
const BASE_URL = "http://localhost:8000/api";

// 1. 강사 등록
async function registerInstructor() {
  const response = await fetch(`${BASE_URL}/auth/register/instructor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: "instructor-1",
      name: "홍길동",
      email: "hong@example.com",
      password: "password123",
    }),
  });
  const data = await response.json();
  return data.access_token;
}

// 2. 강의 업로드
async function uploadCourse(token: string, file: File) {
  const formData = new FormData();
  formData.append("instructor_id", "instructor-1");
  formData.append("course_id", "course-1");
  formData.append("video", file);

  const response = await fetch(`${BASE_URL}/instructor/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  return await response.json();
}

// 3. 처리 상태 확인
async function checkStatus(token: string, courseId: string) {
  const response = await fetch(`${BASE_URL}/status/${courseId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return await response.json();
}

// 4. 챗봇 질의
async function askQuestion(
  token: string,
  courseId: string,
  question: string,
  conversationId?: string
) {
  const response = await fetch(`${BASE_URL}/chat/ask`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      course_id: courseId,
      question,
      conversation_id: conversationId,
    }),
  });
  return await response.json();
}

// 사용 예시
(async () => {
  const token = await registerInstructor();
  console.log("토큰:", token);

  // 파일 업로드 (HTML input에서)
  const fileInput = document.querySelector('input[type="file"]');
  if (fileInput?.files?.[0]) {
    const result = await uploadCourse(token, fileInput.files[0]);
    console.log("업로드 결과:", result);
  }

  // 상태 확인
  const status = await checkStatus(token, "course-1");
  console.log("상태:", status);

  // 챗봇 질의
  const answer = await askQuestion(
    token,
    "course-1",
    "이 강의의 핵심 내용은 무엇인가요?",
    "student-1:course-1"
  );
  console.log("답변:", answer.answer);
})();
```

---

## 주의사항

1. **토큰 만료**: JWT 토큰은 24시간 후 만료됩니다. 만료 시 다시 로그인해야 합니다.

2. **파일 크기**: 대용량 파일 업로드 시 시간이 걸릴 수 있습니다. 처리 상태를 주기적으로 확인하세요.

3. **Rate Limiting**: 시간당 100회 요청 제한이 있습니다. 제한 초과 시 429 에러가 반환됩니다.

4. **권한 체크**: 강사는 자신의 강의만, 학생은 등록한 강의만 접근할 수 있습니다.

5. **대화 히스토리**: `conversation_id`를 동일하게 유지하면 대화 히스토리가 유지됩니다.

6. **비디오 스트리밍**: HTTP Range 요청을 지원하므로 대용량 파일도 효율적으로 스트리밍됩니다.

---

## 추가 리소스

- **Swagger UI**: `http://localhost:8000/docs` - 인터랙티브 API 문서
- **ReDoc**: `http://localhost:8000/redoc` - 대체 API 문서
- **예시 코드**: `server/examples/` 디렉토리 참고

---

## 문제 해결

### 서버가 응답하지 않을 때

1. 서버가 실행 중인지 확인: `curl http://localhost:8000/api/health`
2. 포트가 사용 중인지 확인: `netstat -an | grep 8000` (Linux/Mac)
3. 방화벽 설정 확인

### 인증 오류가 발생할 때

1. 토큰이 올바른지 확인
2. 토큰이 만료되지 않았는지 확인
3. Authorization 헤더 형식 확인: `Bearer <token>`

### 파일 업로드가 실패할 때

1. 파일 크기 확인
2. 파일 형식이 지원되는지 확인
3. 서버 로그 확인

### 처리 상태가 "failed"일 때

1. 서버 로그 확인
2. `OPENAI_API_KEY` 환경 변수 확인
3. 파일 형식 확인

---

**문의사항이나 버그 리포트는 프로젝트 이슈 트래커에 등록해주세요.**
