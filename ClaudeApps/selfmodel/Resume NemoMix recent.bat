@echo off
rem Carries on an interrupted NemoMix training run from its last checkpoint (saved every 30 minutes), then makes the add-on.
title Training Kithylin on NemoMix (recent Telegram chats, resumed)
cd /d "%~dp0.."
set PY="%~dp0..\..\Local Storage\LLM Models\selfmodel\env\Scripts\python.exe"
%PY% -u -m selfmodel.train --resume --run nemomix-recent --base base-nemomix --data data-telegram --embed-cpu --optim adamw8bit --max-len 1408 --hours 24
if errorlevel 1 goto failed
%PY% -u -m selfmodel.make_model --run nemomix-recent --base base-nemomix --lora-on nemomix-unleashed-12b --name kithylin-nemomix-recent --base-title "NemoMix Unleashed 12B (MarinaraSpaghetti, Mistral Nemo merge)" --notes "Kithylin on NemoMix 12B: your Telegram chats, 2022-2026 (replies averaging 8+ words)." --delete-base-weights
echo.
echo Finished. Pick "Kithylin (kithylin-nemomix-recent)" in Kithylin AI.
pause
exit /b
:failed
echo.
echo Training stopped with an error (see above). Run this again to carry on from the last save.
pause
