@echo off
echo ========================================
echo  AI Crop Yield Predictor - Run
echo ========================================
echo.

echo Starting Backend (port 8000)...
start "Backend" cmd /c "cd backend && venv\Scripts\activate && uvicorn app:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend (port 3000)...
start "Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo ========================================
echo  Services starting...
echo ========================================
echo.
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
pause
