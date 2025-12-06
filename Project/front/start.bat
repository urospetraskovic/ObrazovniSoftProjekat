@echo off
REM Start SOLO Quiz Generator Application

echo.
echo ========================================
echo SOLO Taxonomy Quiz Generator
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    exit /b 1
)

REM Check if Python is installed
where py >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org/
    exit /b 1
)

echo Starting backend server...
start "SOLO Backend" cmd /k "cd backend && ..\\.venv\\Scripts\\python.exe app.py"

timeout /t 3 /nobreak

echo Starting frontend server...
start "SOLO Frontend" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo Services starting...
echo Frontend will open at: http://localhost:3000
echo Backend API at: http://localhost:5000
echo ========================================
echo.
pause
