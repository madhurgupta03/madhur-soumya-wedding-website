@echo off
title Soumya ^& Madhur - wedding website
cd /d "%~dp0"
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY if exist "%USERPROFILE%\anaconda3\python.exe" set "PY=%USERPROFILE%\anaconda3\python.exe"
if not defined PY (
  echo Python was not found on this laptop.
  echo Install it from https://www.python.org/downloads/ and run this file again.
  pause
  exit /b 1
)
echo.
echo   Your wedding website is running at:  http://localhost:8000
echo   Keep this window open while you look at it. Close it to stop.
echo.
start "" "http://localhost:8000"
"%PY%" -m http.server 8000
pause
