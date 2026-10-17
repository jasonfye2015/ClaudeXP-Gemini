@echo off
rem Claude Timeline: the SYSTEC Multi-Boot Manager. It runs on the Timeline's own portable Python (the Python folder),
rem so it works from the external SSD on any PC; ClaudeXP's .venv is the fallback on the development PC.
set "PYTHONNOUSERSITE=1"
if exist "%~dp0Python\pythonw.exe" (
    start "" "%~dp0Python\pythonw.exe" "%~dp0ClaudeLauncher\main.py"
) else (
    start "" "%~dp0ClaudeXP\.venv\Scripts\pythonw.exe" "%~dp0ClaudeLauncher\main.py"
)
