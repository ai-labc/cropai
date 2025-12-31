#!/bin/bash
echo "Stopping existing servers..."
pkill -f "uvicorn app.main:app" 2>/dev/null
sleep 2

echo "Starting backend server..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

