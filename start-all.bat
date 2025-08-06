@echo off
echo Starting Vera Full Stack Application...
echo ==================================================

:: Check if Node.js is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: npm is not installed. Please install Node.js first.
    pause
    exit /b 1
)

:: Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo Installing React dependencies...
    cd frontend
    npm install
    cd ..
)

:: Start both servers
echo.
echo Starting servers...
start "Flask Backend" cmd /k "python start_website.py"
timeout /t 2 /nobreak >nul
start "React Frontend" cmd /k "cd frontend && npm run dev"

:: Wait a bit then open browser
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo ===================================================
echo Servers are running!
echo Flask API: http://localhost:5000
echo React App: http://localhost:5173
echo.
echo Close this window to keep servers running.
echo Close the server windows to stop them.
echo ===================================================
pause