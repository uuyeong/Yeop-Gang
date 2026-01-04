# 🧪 처음부터 테스트하는 순서

## 📋 전체 테스트 플로우

### 1️⃣ 환경 설정 (최초 1회)

```bash
# 프로젝트 클론 (처음만)
git clone https://github.com/uuyeong/Yeop-Gang.git
cd Yeop-Gang

# Backend 환경 설정
cd server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend 환경 설정
cd ../client
npm install

# 환경 변수 설정
cd ..
# .env 파일 생성 (README.md 참고)
# OPENAI_API_KEY=your-key-here
```

### 2️⃣ 서버 실행 (매번)

```bash
# 터미널 1: Backend 서버
cd server
source ../.venv/bin/activate
uvicorn main:app --reload

# 터미널 2: Frontend 서버
cd client
npm run dev
```

### 3️⃣ 오디오/비디오 업로드 ⚠️ (필수)

**중요**: 오디오 처리는 서버 시작 시 자동으로 되지 않습니다.  
반드시 `/api/upload`로 파일을 업로드해야 STT 처리가 시작됩니다.

```bash
# 오디오 파일 업로드 (ref/audio/testaudio_1.mp3 사용)
curl -X POST "http://localhost:8000/api/upload" \
  -F "instructor_id=test-instructor-1" \
  -F "course_id=test-course-1" \
  -F "video=@ref/audio/testaudio_1.mp3"

# 또는 비디오 파일 업로드 (ref/video/testvedio_1.mp4 사용)
curl -X POST "http://localhost:8000/api/upload" \
  -F "instructor_id=test-instructor-1" \
  -F "course_id=test-course-1" \
  -F "video=@ref/video/testvedio_1.mp4"
```

### 4️⃣ 처리 상태 확인

```bash
# 상태 확인 (processing → completed 대기)
curl "http://localhost:8000/api/status/test-course-1"

# 응답 예시:
# {
#   "course_id": "test-course-1",
#   "status": "processing",  # 또는 "completed"
#   "progress": 0
# }
```

**처리 시간**: 오디오 파일 크기에 따라 다름 (약 1-5분)

### 5️⃣ 챗봇 테스트

#### 방법 1: 프론트엔드에서 테스트
```
http://localhost:3000/student/play/test-course-1
```

#### 방법 2: API로 직접 테스트
```bash
curl -X POST "http://localhost:8000/api/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "test-course-1",
    "question": "이 강의의 주제는 무엇인가요?",
    "conversation_id": "test-1"
  }'
```

## ❓ 자주 묻는 질문

### Q: 오디오 처리를 매번 해야 하나요?

**A**: 네, 하지만 조건이 있습니다:
- **DB에 저장되어 있고 처리 완료된 course_id**: 다시 업로드 불필요
- **새로운 course_id로 테스트**: 업로드 필요
- **DB를 초기화하거나 새 환경**: 업로드 필요

### Q: 서버 재시작 시 자동으로 처리되나요?

**A**: 아니요. 서버 시작 시 자동 처리되지 않습니다.
- 오디오 처리는 `/api/upload` 엔드포인트 호출 시 Background Task로 시작됩니다
- 서버는 업로드된 파일을 기다립니다

### Q: DB에 이미 데이터가 있으면?

**A**: DB에 course_id가 있고 상태가 `completed`이면:
- 다시 업로드할 필요 없음
- 바로 챗봇 테스트 가능
- `/api/status/{course_id}`로 확인

### Q: 빠른 테스트를 위한 팁

1. **테스트용 course_id 재사용**: 같은 course_id를 계속 사용
2. **DB 백업**: 테스트 데이터가 있는 DB 백업
3. **환경 변수 확인**: OPENAI_API_KEY가 설정되어 있어야 STT 작동

## 🔄 전체 플로우 요약

```
1. 환경 설정 (최초 1회)
   ↓
2. 서버 실행 (매번)
   ↓
3. 파일 업로드 (처음 또는 새로운 course_id)
   ↓
4. 상태 확인 (processing → completed 대기)
   ↓
5. 챗봇 테스트
```

