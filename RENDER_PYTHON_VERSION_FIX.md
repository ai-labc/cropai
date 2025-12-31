# Render Python 버전 설정 가이드

## 문제
Render가 Python 3.13을 사용하고 있어 `pandas==2.1.4`와 호환성 문제가 발생합니다.

## 해결 방법

### 방법 1: Render 대시보드에서 수동 설정 (권장)

1. Render 대시보드 접속
2. 서비스 선택 → **Settings** 탭
3. **Environment** 섹션에서:
   - **Python Version** 드롭다운에서 `3.11` 선택
   - 또는 **Environment Variables**에 추가:
     ```
     PYTHON_VERSION=3.11
     ```
4. **Save Changes** 클릭
5. **Manual Deploy** → **Clear build cache & deploy** 선택

### 방법 2: runtime.txt 파일 확인

`backend/runtime.txt` 파일이 올바른 위치에 있는지 확인:
- Root Directory가 `backend`로 설정되어 있다면: `backend/runtime.txt`에 `python-3.11`이 있어야 함
- 파일 내용: `python-3.11` (줄바꿈 없이)

### 방법 3: render.yaml 확인

`render.yaml`에 `runtime: python-3.11`이 있지만, Render가 이를 인식하지 못할 수 있습니다.
대시보드에서 수동 설정하는 것이 더 확실합니다.

## pandas 버전 업데이트

`pandas==2.1.4`는 Python 3.13과 호환되지 않습니다. 
- Python 3.11 사용 시: `pandas==2.1.4` 유지 가능
- Python 3.13 사용 시: `pandas>=2.2.0` 필요

현재 `requirements.txt`에서 `pandas>=2.2.0`으로 업데이트했습니다.

## 확인 사항

배포 후 로그에서 다음을 확인:
```
==> Installing Python version 3.11.x...
```

Python 3.13.4가 아닌 3.11.x가 설치되어야 합니다.

