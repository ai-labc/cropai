#!/bin/bash
# 완전한 서버 재시작 스크립트

echo "=== 서버 완전 재시작 ==="

# 1. 모든 Python 프로세스 종료
echo "1. Python 프로세스 종료 중..."
pkill -f "uvicorn app.main:app" 2>/dev/null
sleep 2

# 2. Python 캐시 삭제
echo "2. Python 캐시 삭제 중..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
echo "   캐시 삭제 완료"

# 3. 서버 시작
echo "3. 서버 시작 중..."
source venv/Scripts/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

