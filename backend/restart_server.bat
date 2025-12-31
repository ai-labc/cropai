@echo off
echo Stopping existing servers...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting backend server...
cd backend
call venv\Scripts\activate.bat
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

