@echo off
rem Fine-tunes Gemma 3 4B on your chats overnight (about 7.5 hours on a GTX 1080 Ti).
rem Close the Timeline computers first: training needs the graphics card to itself.
rem It saves progress every 30 minutes; if it stops, run "Resume training.bat".
title Training the model of you
cd /d "%~dp0.."
"%~dp0..\..\Local Storage\LLM Models\selfmodel\env\Scripts\python.exe" -u -m selfmodel.train --hours 8.5
echo.
echo Finished. The result is in Local Storage\LLM Models\selfmodel\adapter
pause
