ClaudeApps - the AI apps and Python Studio, on every computer
==============================================================

  claudeai/          ClaudeAI - chat with the local models (pictures, thinking)
  kithylinai/        Kithylin AI - chat with Kithylin, played by your own fine-tuned models, over Kithylin's art;
                     codes encoder/decoder, gallery, editable system prompts. Keeps its art, models and chats in
                     its own folder so it can be lifted out as a standalone program (see its README)
  selfmodel/         training a model of you from your chat logs: export.py, train.py, make_model.py
  soulsong/          Soul and Song - the Companion Project (Local Storage\Projects\AI LLM Txt Files) automated:
                     mind files L1-L6, memories made, stamped, filed and distilled 7:7:7, on any local model
  manual/            the Claude Timeline Manual's viewer: the Markdown pages in Manual\ (at the top of the Timeline),
                     read in each computer's own window, from the launcher's MANUAL button, or python -m manual
  copilotai/         CopilotAI - chat by text or voice, with pictures from Image Creator
  copilot_voice.py   Copilot Voice - speech in and out (Whisper and Piper; copilot_voice_worker.py runs them)
  imagegen.py        Copilot Image Creator - pictures from a description (imagegen_worker.py runs Stable Diffusion)
  voicecatalog.py    the voices CopilotAI can speak with
  pystudio/          Copilot Python Studio - write, check, debug and run Python offline, with an AI Helper
  cesscr/            the Claude Entertainment System as a real Windows screen saver (.scr) - see its README
  requirements-*.txt what the voice and picture engines install into their own Python in Local Storage

They use the Timeline's shared AI engine (ClaudeCore/claudecore/ai) and talk to the computer only through
ClaudeCore's host (see ClaudeGames/README.txt): its windows, dialogs, tray, printer, Open dialog, file manager,
My Documents and My Pictures. Chats and settings are each computer's own (host.data).
