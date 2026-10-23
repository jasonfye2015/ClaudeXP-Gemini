@echo off
rem Carries on an interrupted NemoMix training run from its last checkpoint (saved every 30 minutes), then makes the add-on.
title Training Kithylin on NemoMix (adult roleplay, resumed)
cd /d "%~dp0.."
set PY="%~dp0..\..\Local Storage\LLM Models\selfmodel\env\Scripts\python.exe"
%PY% -u -m selfmodel.train --resume --run nemomix-adult --base base-nemomix --data data-adult --embed-cpu --optim adamw8bit --max-len 1408 --hours 22
if errorlevel 1 goto failed
%PY% -u -m selfmodel.make_model --run nemomix-adult --base base-nemomix --lora-on nemomix-unleashed-12b --name kithylin-nemomix-adult --base-title "NemoMix Unleashed 12B (MarinaraSpaghetti, Mistral Nemo merge)" --notes "Kithylin on NemoMix 12B: your longer adult roleplay sessions (20+ of your turns)." --delete-base-weights
echo.
echo Finished. Pick "Kithylin (kithylin-nemomix-adult)" in Kithylin AI.
pause
exit /b
:failed
echo.
echo Training stopped with an error (see above). Run this again to carry on from the last save.
pause
