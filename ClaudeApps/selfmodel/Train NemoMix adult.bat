@echo off
rem Fine-tunes NemoMix Unleashed 12B on your longer adult roleplay sessions (about 22 hours on a GTX 1080 Ti).
rem Close the Timeline computers and Kithylin AI first: training needs the graphics card to itself.
rem It saves progress every 30 minutes; if it stops, run "Resume NemoMix adult.bat".
rem When it finishes, it makes the Kithylin AI add-on and deletes NemoMix's 24 GB of full weights.
title Training Kithylin on NemoMix (adult roleplay)
cd /d "%~dp0.."
set PY="%~dp0..\..\Local Storage\LLM Models\selfmodel\env\Scripts\python.exe"
%PY% -u -m selfmodel.train --run nemomix-adult --base base-nemomix --data data-adult --embed-cpu --optim adamw8bit --max-len 1408 --hours 22
if errorlevel 1 goto failed
%PY% -u -m selfmodel.make_model --run nemomix-adult --base base-nemomix --lora-on nemomix-unleashed-12b --name kithylin-nemomix-adult --base-title "NemoMix Unleashed 12B (MarinaraSpaghetti, Mistral Nemo merge)" --notes "Kithylin on NemoMix 12B: your longer adult roleplay sessions (20+ of your turns)." --delete-base-weights
echo.
echo Finished. Pick "Kithylin (kithylin-nemomix-adult)" in Kithylin AI.
pause
exit /b
:failed
echo.
echo Training stopped with an error (see above). Run "Resume NemoMix adult.bat" to carry on from the last save.
pause
