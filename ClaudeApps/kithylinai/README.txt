Kithylin AI - chat with Kithylin the Angelic Husky
==================================================

Kithylin is played by your own fine-tuned models (ClaudeApps\selfmodel trains them from your chat logs). The window
is a chat over Kithylin's art: your words in white, his in light blue, and the system's in purple - what system
prompt and codes the model was given, and what the engine is doing ("Now loading ...").

  Chat            Enter sends, Shift+Enter is a new line, Ctrl+B / Ctrl+I for **bold** and *italic*. New chat,
                  Save chat... (a named copy plus a .txt), Open chat..., Stop.
  Kithylin's Art  the gallery: folders, thumbnails, a viewer (arrow keys, Esc), "Use as chat background".
  Codes           the Furry Code 2.0 / YIFF Code 3.0 encoder and decoder. "Use these codes for Kithylin" rewrites
                  the codes part of the system prompt; "Decode into the chat" writes out what a code says.
  Model Details   the card for the model picked at the top: what it learned from (general chatting, roleplay,
                  adult - by share of the text), which years, services and people, how the training went, and
                  snippets of the training conversations (the adult ones behind a tick box). Kithylin models get
                  a card.json from selfmodel.make_model (or python -m selfmodel.card MODEL_FOLDER).
  Settings        the model engine, context and temperature; the look (your name, text size, background slideshow);
                  the two editable system prompts - who Kithylin is, and his codes - each with a default to go
                  back to; and Reset.

Everything it uses stays in this folder, so the program can be lifted out whole:

  assets\         the icon (your account picture)
  Art\            Kithylin's Art and its thumbnails + index.json. Built once by build_art.py from
                  Local Storage\Misc Personal Image Folders\AI Kithy. Not in git (personal).
  Models\         the Kithylin models: <name>\<name>-Q4_K_M.gguf + info.json, made by selfmodel.make_model.
                  Not in git. The Timeline's models in Local Storage\LLM Models\models are offered too.
  Engine\         optional: your own llama.cpp build (llama-server.exe + DLLs) for running away from the Timeline.
                  Otherwise the Timeline's build in Local Storage\LLM Models\llama.cpp is used.
  Data\           settings.json, chats\ (every chat, autosaved), saved\ (the ones you named), llama-server.log.
                  Not in git.

Running it
  In the Timeline: Start > All Programs > Kithylin AI on any of the three computers.
  Standalone: "Kithylin AI.bat", or  Python\python.exe -m kithylinai  from ClaudeApps.
  To spin it off: copy ClaudeApps\kithylinai plus ClaudeCore\claudecore\furcodes (for the codes page; put
  ClaudeCore on the path or beside it), a Python with PySide6, and a llama.cpp build in Engine\.

Models and the graphics card
  A Kithylin model gets a llama-server of its own here. Inside the Timeline, a model from Local Storage is run by
  the Timeline's engine router instead, so it shares the card with the residents. "CPU only" in Settings leaves the
  card alone entirely (slow). While a model is training on the card, don't load one here.
