@echo off
echo.
echo ===============================================
echo   Student Performance Predictor
echo ===============================================
echo.
echo [1/2] Installing required packages...
pip install -r requirements.txt
echo.
echo [2/2] Starting server...
echo.
echo   Open your browser and go to:
echo   http://localhost:5000
echo.
python app.py
pause
