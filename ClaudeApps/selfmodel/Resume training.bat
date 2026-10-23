@echo off
rem Carries on an interrupted training run from its last checkpoint (saved every 30 minutes).
title Training the model of you (resumed)
cd /d "%~dp0.."
"%~dp0..\..\Local Storage\LLM Models\selfmodel\env\Scripts\python.exe" -u -m selfmodel.train --resume --hours 8.5
echo.
echo Finished. The result is in Local Storage\LLM Models\selfmodel\adapter
pause
