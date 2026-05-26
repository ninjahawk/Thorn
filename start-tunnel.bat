@echo off
echo ============================================
echo  Starting Emmi Chat Backend + Tunnel
echo ============================================
echo.

REM Ollama needs CORS to accept requests from GitHub Pages
set OLLAMA_ORIGINS=*

echo [1/2] Starting Ollama with CORS enabled...
start /B ollama serve

timeout /t 3 /nobreak >nul

echo [2/2] Starting Cloudflare Tunnel...
echo.
echo  Copy the URL below and save it in the app settings!
echo  (It will look like https://something-random.trycloudflare.com)
echo.

cloudflared tunnel --url http://localhost:11434

pause
