@echo off
REM Backend server startup script for Windows

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

