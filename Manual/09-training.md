# 9. Training a new Kithylin

A Kithylin model is a base language model fine-tuned on your own conversations, so that it answers the way you do.
The tools are in `ClaudeApps\selfmodel`; the material, the working files and the results in
`Local Storage\LLM Models\selfmodel`. It all runs on the GTX 1080 Ti, overnight or longer.

## The pipeline

```
your chat logs  ──►  the index  ──►  training conversations  ──►  the adapter  ──►  a Kithylin model
Text Logs\          chatlogs.index    export.py / telegram.py       train.py           make_model.py
                                      data*\train.jsonl             runs\<name>\        kithylinai\Models\<name>\
```

1. **Index the logs.** `python -m chatlogs.index` from `ClaudeArchive` reads every log in `Text Logs` into
   `Text Logs\_Index\chatlogs.sqlite`, de-duplicating the same conversation across backups and clients.
2. **Export training conversations.** `python -m selfmodel.export` from `ClaudeApps` cuts each chat into sessions
   (a gap of more than half an hour starts a new one), makes the other person's lines "user" turns and yours
   "assistant" turns, replaces links, e-mail addresses and phone numbers with placeholders, and writes
   `data\train.jsonl` and `val.jsonl` with a `stats.json`. The system line of each conversation says who you are,
   where, with whom and when, so a model can be asked for "you on AIM in 2005". Options choose what goes in:
   `--years 2004-2011`, `--kinds adult,roleplay`, `--min-turns 20` (only the longer sessions), `--min-avg-words 10`,
   `--per-contact 3000` (so one long friendship doesn't drown out the rest), `--tokens` (the overall size). For a
   Telegram export, `python -m selfmodel.telegram` does the same from `Text Logs\telegram\result.json`.
3. **Train.** `train.py` fine-tunes the base with QLoRA: the base's weights are frozen in 4-bit, and a small adapter
   learns on top. It saves a checkpoint every 30 minutes, measures the held-out loss as it goes, and stops at
   `--hours`. The result is the adapter in `runs\<name>\adapter` (or `adapter\` for the Gemma run).
4. **Make the model.** `make_model.py` turns the adapter into something the Timeline can run, and writes the
   `info.json` and the Model Details card (`card.json`, with other people's names hidden). For a small base (Gemma 3
   4B) it merges the adapter into the base and quantises to a whole 2.5 GB `.gguf`. For a 12B that would need 50 GB
   of working space, so instead `--lora-on` makes a small GGUF add-on that llama-server applies on top of the base's
   own file at load time.

Each kind of conversation is judged on the whole session: **general**, **roleplay** (a good share of the turns are
actions - *wags*, /me) or **adult** (several explicit words). Adult wins over roleplay.

## The bat files

You don't have to type any of that. In `ClaudeApps\selfmodel`:

| Bat | What it does |
|---|---|
| **Train overnight.bat** | Gemma 3 4B on all your logs, about 7.5 hours; the result is `adapter\` (then run `make_model` yourself) |
| **Train NemoMix adult.bat** | NemoMix 12B on your longer adult roleplays (20+ of your turns, 10+ words a reply), about 22 hours, then makes `kithylin-nemomix-adult` and deletes NemoMix's 24 GB of full weights |
| **Train NemoMix recent.bat** | NemoMix 12B on your 2022-2026 Telegram chats (8+ words a reply), about 19 hours, then makes `kithylin-nemomix-recent` and deletes the full weights |
| **Resume ....bat** | Carries the matching run on from its last checkpoint. If training stopped - the drive dropped, the PC restarted, the window was closed - run this. Nothing is lost but the last half hour |

A new run needs the base's full weights (not the GGUF): `python -m selfmodel.fetch nemomix` downloads NemoMix
Unleashed 12B (24.5 GB, Apache 2.0) into `selfmodel\base-nemomix`; `fetch` with no argument gets Gemma 3 4B into
`base\`. The training Python lives in `selfmodel\env` (PyTorch, bitsandbytes, PEFT); the bats use it.

**Before you start:** close the computers and Kithylin AI (the card must be free), make sure the SSD is on a USB 3
port and USB selective suspend is off, and have about 60 GB free on the drive for the base weights plus checkpoints.

## The three models so far

| | kithylin-v1 | kithylin-nemomix-adult | kithylin-nemomix-recent |
|---|---|---|---|
| Base | Gemma 3 4B | NemoMix Unleashed 12B | NemoMix Unleashed 12B |
| Material | every log, 1999-2022: 10,936 conversations, 3.9M tokens, 96,172 of your turns | adult sessions with 20+ of your turns, averaging 10+ words: 3,695 conversations, 2.4M tokens, 39,558 turns | Telegram 2022-2026, replies averaging 8+ words: 10,294 conversations, 3.3M tokens, 64,228 turns (92% general, 8% adult, 1% roleplay) |
| Held-out loss | 7.09 to 2.63 | 2.75 to 2.12 | 2.95 to 2.21 at step 450 (finished 25 October 2026) |
| Took | about 7 hours | about 12 hours | about 24 hours |
| Result | a 2.5 GB model | a 114 MB add-on | an add-on |

The loss is how surprised the model is by your real replies in conversations it never saw; lower is more like you.
Starting lower (2.75 against 7.09) is NemoMix already knowing how to roleplay.

**What Telegram taught us about you:** 287,810 messages from 2015 to 2026; joined into replies, the median reply is
7 words in 2025-26. One- to three-word replies teach a model nothing but to be terse, hence the "8+ words" filter.

## What it took to fit a 12B on an 11 GB card

For whoever reads `train.py` next:

- The card is Pascal: about 64 times slower at half precision, and Gemma overflows in it anyway, so everything is
  computed in 32-bit float with the frozen weights in 4-bit (NF4).
- The output layer over a 262k (Gemma) or 131k (Mistral) vocabulary is the memory hog. It runs only on the positions
  being learned (your replies), in chunks of 128 recomputed in the backward pass, and for the 12B it's kept as eight
  4-bit slices (`--embed-cpu` also keeps the vocabulary table in system RAM, where a lookup costs nothing).
- The 8-bit AdamW optimiser (`--optim adamw8bit`) halves the optimiser's memory.
- Mistral-family models train in ChatML, the format they're run with; Gemma in its own.
- Peak 8.0 GB on the card at about 71 tokens a second for the 12B. If it ever quietly turns thirty times slower, it
  has spilled into system RAM: something else is on the card.
- `train.py` tells Windows to stay awake and touches a file on the drive every minute, after the drive went to
  sleep mid-run once.

## Adding new material later

1. Put the logs where the index can read them: Pidgin/Trillian/mIRC logs anywhere under `Text Logs`; a new Telegram
   export (Telegram Desktop > Settings > Advanced > Export Telegram data, format **Machine-readable JSON**) replaces
   `Text Logs\telegram\result.json`.
2. Rebuild the index (step 1 above) if the logs changed; the Telegram importer reads `result.json` directly.
3. Export a data set with the options you want, into a folder of its own (`--out`), and copy a Train bat, changing
   `--run`, `--data` and the model's `--name` and `--notes`.
4. Train, let the bat make the model, and pick it in Kithylin AI.

A Kithylin model is personal: it was made from your private conversations, and the card holds snippets of them. The
`Models` folder is not in git; keep it to yourself.
