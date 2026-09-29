@echo off
echo ========================================
echo  AI Crop Yield Predictor - Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo [2/3] Installing dependencies...
pip install -r requirements.txt

echo [3/3] Training model...
python train_model.py

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo To run the backend:
echo   venv\Scripts\activate
echo   uvicorn app:app --reload --port 8000
echo.
echo To run the frontend (in another terminal):
echo   cd frontend
echo   npm install
echo   npm run dev
echo.
pause
