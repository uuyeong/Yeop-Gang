#!/usr/bin/env python3
"""
API 키 디버깅 스크립트
실제로 어떤 API 키가 로드되고 있는지 확인합니다.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 찾기
project_root = Path(__file__).resolve().parents[1]
env_path = project_root / ".env"

print("=" * 60)
print("API 키 디버깅")
print("=" * 60)
print(f"\n1. .env 파일 경로: {env_path}")
print(f"   파일 존재 여부: {env_path.exists()}")

if env_path.exists():
    print(f"   파일 크기: {env_path.stat().st_size} bytes")
    print(f"   파일 수정 시간: {env_path.stat().st_mtime}")
    
    # .env 파일 내용 확인 (API 키만)
    with open(env_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line.startswith('OPENAI_API_KEY'):
                if '=' in line:
                    key_part = line.split('=', 1)[1].strip()
                    # 따옴표 제거
                    key_part = key_part.strip('"').strip("'")
                    if key_part:
                        preview = key_part[:10] + "..." + key_part[-4:] if len(key_part) > 14 else "***"
                        print(f"\n2. .env 파일의 OPENAI_API_KEY (라인 {line_num}):")
                        print(f"   {line.split('=')[0]}=... (length: {len(key_part)})")
                        print(f"   미리보기: {preview}")
                        print(f"   형식 확인: {'✅ sk-' + key_part[3] if key_part.startswith('sk-') else '⚠️ sk-로 시작하지 않음'}")
                    else:
                        print(f"\n2. .env 파일의 OPENAI_API_KEY (라인 {line_num}): ⚠️ 값이 비어있음")
                else:
                    print(f"\n2. .env 파일의 OPENAI_API_KEY (라인 {line_num}): ⚠️ 형식이 잘못됨 (=' 없음)")
else:
    print("\n2. .env 파일을 찾을 수 없습니다!")

# load_dotenv 실행
print("\n3. load_dotenv() 실행:")
try:
    load_dotenv(dotenv_path=env_path, override=True)
    print("   ✅ load_dotenv() 성공")
except Exception as e:
    print(f"   ⚠️ load_dotenv() 실패: {e}")

# os.environ에서 확인
print("\n4. os.environ에서 확인:")
env_key = os.environ.get("OPENAI_API_KEY")
if env_key:
    preview = env_key[:10] + "..." + env_key[-4:] if len(env_key) > 14 else "***"
    print(f"   ✅ OPENAI_API_KEY found: {preview} (length: {len(env_key)})")
    print(f"   형식: {'✅ sk-' + env_key[3] if env_key.startswith('sk-') else '⚠️ sk-로 시작하지 않음'}")
else:
    print("   ⚠️ OPENAI_API_KEY not found in os.environ")

# AISettings로 확인
print("\n5. AISettings로 확인:")
try:
    from ai.config import AISettings
    settings = AISettings()
    if settings.openai_api_key:
        preview = settings.openai_api_key[:10] + "..." + settings.openai_api_key[-4:] if len(settings.openai_api_key) > 14 else "***"
        print(f"   ✅ AISettings.openai_api_key: {preview} (length: {len(settings.openai_api_key)})")
        print(f"   형식: {'✅ sk-' + settings.openai_api_key[3] if settings.openai_api_key.startswith('sk-') else '⚠️ sk-로 시작하지 않음'}")
        
        # os.environ과 비교
        if settings.openai_api_key == env_key:
            print(f"   ✅ AISettings의 키가 os.environ과 일치합니다")
        else:
            print(f"   ⚠️ AISettings의 키가 os.environ과 다릅니다!")
            if env_key:
                env_preview = env_key[:10] + "..." + env_key[-4:] if len(env_key) > 14 else "***"
                print(f"      os.environ: {env_preview}")
                print(f"      AISettings: {preview}")
    else:
        print("   ⚠️ AISettings.openai_api_key is None or empty")
except Exception as e:
    print(f"   ⚠️ AISettings 초기화 실패: {e}")
    import traceback
    traceback.print_exc()

# OpenAI API 테스트 (선택사항)
print("\n6. OpenAI API 테스트 (선택사항):")
test_key = env_key or (settings.openai_api_key if 'settings' in locals() and settings.openai_api_key else None)
if test_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=test_key)
        # 간단한 모델 목록 조회로 API 키 유효성 확인
        models = client.models.list()
        print(f"   ✅ API 키가 유효합니다! 사용 가능한 모델 수: {len(models.data)}")
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            print(f"   ⚠️ API 키가 유효하지 않습니다 (401 Unauthorized)")
        elif "429" in error_msg or "rate_limit" in error_msg.lower():
            print(f"   ⚠️ API 키는 유효하지만 할당량이 초과되었습니다 (429 Rate Limit)")
        else:
            print(f"   ⚠️ API 테스트 실패: {error_msg}")
else:
    print("   ⚠️ API 키가 없어서 테스트할 수 없습니다")

print("\n" + "=" * 60)
print("디버깅 완료")
print("=" * 60)

