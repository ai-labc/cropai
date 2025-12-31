#!/usr/bin/env python3
"""
서버 강제 재로드를 위한 스크립트
main.py 파일을 수정하여 서버가 변경을 감지하도록 함
"""
import os
import time

main_py = "app/main.py"
file_path = os.path.join(os.path.dirname(__file__), main_py)

if os.path.exists(file_path):
    # 파일의 마지막 수정 시간을 변경
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 주석 추가/제거로 파일 변경
    if "# Force reload" in content:
        content = content.replace("# Force reload\n", "")
    else:
        content = "# Force reload\n" + content
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] {main_py} 파일이 수정되었습니다.")
    print("서버가 자동으로 재로드되어야 합니다.")
    print("3초 후 테스트하세요...")
else:
    print(f"[ERROR] {main_py} 파일을 찾을 수 없습니다.")

