ClaudeApps - the AI apps and Python Studio, on every computer
==============================================================

  claudeai/          ClaudeAI - chat with the local models (pictures, thinking)
  copilotai/         CopilotAI - chat by text or voice, with pictures from Image Creator
  copilot_voice.py   Copilot Voice - speech in and out (Whisper and Piper; copilot_voice_worker.py runs them)
  imagegen.py        Copilot Image Creator - pictures from a description (imagegen_worker.py runs Stable Diffusion)
  voicecatalog.py    the voices CopilotAI can speak with
  pystudio/          Copilot Python Studio - write, check, debug and run Python offline, with an AI Helper
  requirements-*.txt what the voice and picture engines install into their own Python in Local Storage

They use the Timeline's shared AI engine (ClaudeCore/claudecore/ai) and talk to the computer only through
ClaudeCore's host (see ClaudeGames/README.txt): its windows, dialogs, tray, printer, Open dialog, file manager,
My Documents and My Pictures. Chats and settings are each computer's own (host.data).
