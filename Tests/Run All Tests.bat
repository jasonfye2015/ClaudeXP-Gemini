@echo off
rem Check everything: the Claude Timeline's tests (see Tests\README.md). Add --slow to boot each computer as well.
rem It runs on the Timeline's own portable Python, like the launcher; ClaudeXP's .venv is the fallback.
cd /d "%~dp0.."
set "PYTHONNOUSERSITE=1"
if exist "Python\python.exe" (
    "Python\python.exe" Tests\run.py %*
) else (
    "ClaudeXP\.venv\Scripts\python.exe" Tests\run.py %*
)
echo.
pause
