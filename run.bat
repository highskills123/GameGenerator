@echo off
REM ──────────────────────────────────────────────────────────────
REM  Aibase — One-click startup script for Windows
REM
REM  IMPORTANT: Run this from inside the Aibase folder, e.g.:
REM    cd C:\Users\high\Aibase
REM    run.bat --ngrok
REM
REM  Usage:
REM    run.bat             -- local only  (http://localhost:5000)
REM    run.bat --ngrok     -- public URL  (share with anyone)
REM    run.bat --port 8080 --ngrok
REM
REM  NOTE: Do NOT use "start.bat" — "start" is a Windows built-in
REM        command and will behave unexpectedly. Use "run.bat" instead.
REM
REM  To use a static/reserved ngrok domain, edit your .env file first:
REM    NGROK_AUTHTOKEN=your_authtoken_here
REM    NGROK_DOMAIN=costless-dorthy-unmeanderingly.ngrok-free.dev
REM ──────────────────────────────────────────────────────────────

echo.
echo   ^<^< Aibase -- starting up... ^>^>
echo.

REM ── 1. Install Python dependencies ──────────────────────────
echo [1/3] Installing Python dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo      ERROR: pip install failed. Make sure Python and pip are installed.
    exit /b 1
)
echo       Dependencies ready

REM ── 2. Check that Ollama is running ─────────────────────────
echo [2/3] Checking Ollama...
curl -sf http://localhost:11434/ >nul 2>&1
if errorlevel 1 (
    echo       ERROR: Cannot reach Ollama at http://localhost:11434
    echo.
    echo   Ollama must be running before the server can generate code.
    echo   Install it from  https://ollama.com  then open a new terminal and run:
    echo.
    echo       ollama serve
    echo       ollama pull qwen2.5-coder:7b     ^(first time only^)
    echo.
    echo   Then re-run this script.
    exit /b 1
)
echo       Ollama is running

REM ── 3. Start the API server ──────────────────────────────────
echo [3/3] Starting Aibase API server...
echo.

REM Pass all arguments through to api_server.py (e.g. --ngrok, --port)
python api_server.py %*


echo.
echo   ^<^< Aibase -- starting up... ^>^>
echo.

REM ── 1. Install Python dependencies ──────────────────────────
echo [1/3] Installing Python dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo      ERROR: pip install failed. Make sure Python and pip are installed.
    exit /b 1
)
echo       Dependencies ready

REM ── 2. Check that Ollama is running ─────────────────────────
echo [2/3] Checking Ollama...
curl -sf http://localhost:11434/ >nul 2>&1
if errorlevel 1 (
    echo       ERROR: Cannot reach Ollama at http://localhost:11434
    echo.
    echo   Ollama must be running before the server can generate code.
    echo   Install it from  https://ollama.com  then open a new terminal and run:
    echo.
    echo       ollama serve
    echo       ollama pull qwen2.5-coder:7b     ^(first time only^)
    echo.
    echo   Then re-run this script.
    exit /b 1
)
echo       Ollama is running

REM ── 3. Start the API server ──────────────────────────────────
echo [3/3] Starting Aibase API server...
echo.

REM Pass all arguments through to api_server.py (e.g. --ngrok, --port)
python api_server.py %*
