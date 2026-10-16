# PawPrints MUCK / MushClient

## mIRC / FurNet

Open **Start → Programs → mIRC** (or Run `mirc`). It automatically signs in to
the simulated **FurNet.IRC:6667** under the selected Windows fursona's name and
joins `#furnet`. It never connects to an external IRC server. The supplied
network, MOTD, five channels, icon, and eligible regulars are installed locally.
Channel tabs, operator-marked nick lists, private-message tabs, topics, and
resident arrivals/departures are supported.

Try `/join #gaming`, `/list`, `/names`, `/whois Nick`, `/msg Nick hello`,
`/query Nick`, `/me waves`, `/nick NewNick`, `/away Away from keyboard`, `/away`
to return, `/part`, `/disconnect`, `/connect`, and `/help`. Double-click a nick
to open a private conversation. Resident replies use the existing direct local
model; server commands and navigation work without it. FurBot supports `!help`
and `!time` without a model. Local NickServ registration needs no password.

The tray icon is present only while mIRC is running, including when minimized.
Green flashes for sending and red for receiving. Its menu opens, connects,
disconnects, changes away state or nickname, closes, and exits the client.
Closing removes the icon; launching again reconnects automatically. During a
simulated outage, the client disconnects and reconnects when service returns,
but failed model requests are not retried. Simulation pauses while closed.

Only verified 21+ humans participate. Zeph (17), Gill (20), and unverified
idle-name entries are filtered without changing source files. Bots remain
available. Imported 2001–2002 network/topic references are preserved.
Chat scrollback and short model context are session-only, isolated by fursona
and by public channel versus private message. The existing LLM logger records
model prompts and replies for diagnostics.

Open **Start → Programs → MushClient**. Its paw-shaped notification-area icon
appears only while the program is open, including when minimized; it is not
loaded at Windows startup. The client connects to the local **PawPrints MUCK** simulation, not a real
external server. Type `connect Kithylin` when Kithylin is the selected Windows
fursona, substituting the selected fursona's name as needed. There is no password.
The character description is copied from that fursona's Windows setup biography.

Use `look`, `who`, map exits such as `out` and `north`, `home`, `say Hello!`,
`pose waves`, `page Name=Hello!`, `examine Name`, and `help`. `@desc` changes only
the current session's player description; reconnecting restores the setup
description. `@describe here=...` can customize the player's own den for that
session. The yellow tray LED blinks for MUCK activity; its menu opens, connects,
disconnects, closes, or exits the client. Closing or exiting removes the tray icon
until the client is launched again.

Supplied regulars and background profiles are combined by name, and the existing
adult MSN contacts can appear in the world. Residents arrive, leave, and move
while the client is connected. Simulation ticks pause during outages, maintenance,
and a pending MUCK reply; no closed-time catch-up is performed. Resident responses
use the configured direct local model through the same llama.cpp service as MSN.
Commands and navigation do not require a model, and missing model access produces
an explicit message rather than fabricated chat. Private pages and public-room
conversation context are separate and scoped to the active fursona.

The source files are preserved, but Bubbles (19), Pixel (16), and Gill (20) are
excluded by the project's 21+ policy. SleepyStripes has no confirmed age and is
also excluded pending age information. MushClient's scrollback and short chat
context are session-only; the existing LLM activity logger still records model
prompts and output.

# Supplied MSN Messenger update

The desktop Messenger entry now opens the supplied image-backed MSN contact list.
Double-click a contact to open a separate conversation window; each has its own
taskbar button, while all conversations use the shared local AI service and queue.
Opening the same contact again brings its existing window forward.

- The supplied 34 close-contact profiles, buddy icons, artwork, photos and captions
  are installed under `assets/msn/`. Their furry screen names are used online.
- MSN starts with those 34 people plus 150 background community members, now using
  fandom-style handles. The previous 50 starter contacts remain in Furry Directory
  and can be shown with **Contacts → Show previous starter contacts**. Their stable
  IDs and saved chats are preserved, never reassigned to the new people.
- Online/offline groups have counts, searchable contact rows, two icons per row,
  changing presence, activity notices, and block/unblock actions. Away messages and
  the user's status are available through the header or File menu. Presence runs
  without an LLM, pauses with background slowdowns, and stops at desktop shutdown.
- Original JSON presence probabilities/durations and timezone-aware sleep schedules
  are used. Automatic greeting/idle trigger scripts and delayed-reply scripts are
  retained in the source data but are **not yet executed**; the app does not generate
  unsolicited model work simply because the roster opens.
- Chats retain the existing saving, fursona isolation, import/export, corruption
  warnings, context budgeting, approved notes, and recovery controls. Open
  **Tools → Conversation details / AI context** for the advanced controls.
- The composer supports multiple lines: **Enter** sends; **Shift+Enter** inserts
  a new line. Font, text color, emoticons, local backgrounds, and a simple native
  wink effect are available. Font/background choices currently apply to that
  open window, rather than being saved as per-message formatting.
- Contacts can share installed pictures using an allowlisted `[share:filename]`
  marker in their model reply. Clicking its link opens the local picture viewer.
  Pictures are not uploaded to the text model; supplied captions provide context.
  Galleries and full profiles also appear in Furry Directory.
- The last received date is saved per fursona in the fixed 2011 calendar. Older
  transcripts without timestamps show no invented date.
- The supplied default ad does nothing when clicked. An installed ad with a URL
  opens the local-only web viewer, not a real browser. Local pages can live at
  `Storage/Web/<hostname>/index.html`; remote resources are blocked. No additional
  ads were supplied, so the default remains in rotation.
- The envelope can flash through the unread-mail hook; email integration itself is
  not installed yet. Invite, file transfers, webcam, audio, activities, games and
  creation of new contacts remain clearly marked for later, as the supplied README
  requests. The wink is a simple native effect, not a full animated-sticker engine.

MSN status, block choices and received-date metadata live in the active fursona's
`Storage/Profiles/<profile-id>/msn.json`, and are wiped with user data during Format
& Reinstall. Damaged settings are reported and preserved rather than overwritten.
The new contacts need **no reformat** to appear. Supplied age-only profiles retain
their stated 2011 age without an invented birthday; CyberianHusky's exact age is
unspecified and is shown as 21+ under the project's adult-only policy.

# Windows 7: 2011

A private, standalone Python slice-of-life simulator for a home PC frozen in
2011. The displayed month, day, weekday, and time follow the computer's local
clock; the displayed year stays fixed at 2011. Simulation work pauses while the
program is closed.

## Run

The GUI uses PySide6. From the workspace root:

```bash
uv sync
uv run python main.py
```

On Windows, run `win7_2011\setup_windows.bat` once, then
`win7_2011\run_windows.bat`.

### Recover damaged BIOS settings

Successful BIOS saves maintain `Storage/System/bios.backup.json`. Startup uses
defaults if `bios.json` is damaged or unreadable; it does not automatically
replace the file with the backup. Press Delete to enter BIOS setup, then F9
to explicitly restore the known-good copy and confirm the prompt. Recovery
preserves the exact original bytes in a unique `bios.damaged-*.json` file before
replacing `bios.json`, and leaves BIOS passwords unchanged. A missing or invalid
backup, or failure to preserve the original, stops recovery with an error.
F10 can instead save the current choices, but after a settings load failure it
requires confirmation and preserves the original first. Escape leaves the files
unchanged.

## First playable slice

- AMI/ASUS POST with supplied American Megatrends, ENERGY STAR, Gemma 4, and
  Gemini marks, a timed memory check and POST beep; press Space to skip directly to the
  Windows boot animation. Then continue to first-run account setup or a
  Windows 7-style profile login with the supplied background and account image.
- Login accepts any or no password, supports Enter to continue, and includes
  the supplied Switch User and power controls. Switch User opens the profile
  selection screen; choosing a profile saves it and returns to login. Restart,
  sleep, and shutdown are available from the power menu on both screens.
- First-run setup is prefilled with the six supplied fursonas and their
  tentative profile details. Their listed ages are interpreted as ages reached
  in 2011; birth years are derived from those ages and month/day values. The
  user may revise profiles during setup, but saved profile details are fixed.
- The profile selection screen shows saved profiles only, with their supplied
  icons, hover frames, and sounds. It switches between profiles without
  creating or editing them. Changing saved identity details requires the
  format-and-reinstall flow, which clears user-owned details, progress, and
  logs.
- One desktop account can be linked to a shared online name and hold multiple
  fursona profiles
- Fursona profiles require a date of birth that makes the character at least
  21 for the entire 2011 simulation year
- Windows-style desktop, Start menu, taskbar, 2011-locked clock, a shared
  200-person adult Furry Directory, Notepad, Calculator, Paint, WordPad, and a shutdown/restart/
  recovery sequence with a delayed safe-to-power-off screen
- Windows Live Messenger and Furry Directory using the same 200 stable,
  detailed fictional adult profiles (50 close contacts and 150 community
  members), shared local AI configuration, honest provider errors, and in-session service
  disconnections/maintenance/slowdowns
- Messenger's **Export saved conversation…** and **Export all saved chats…**
  save readable JSON at a location you choose, even while offline. Exports
  include the active fursona's saved ID, contact names/IDs and ordered messages
  with user/assistant roles. Both export buttons include only that fursona's chats.
  Only messages already saved on disk are included. Choose a location outside
  simulator Storage; keep the file on another drive before formatting the
  computer. Cancelled or failed exports leave local histories unchanged.
- After reinstalling, select the owning fursona and use **Import saved chats…**
  to choose an exported JSON file. Preview every contact and its messages, then
  explicitly confirm the owner (the old saved fursona ID may differ after reinstall).
  Choose to keep existing chats, append imported messages, or replace matching
  chats. Keeping existing chats is the default; appending can create duplicates.
  Imports work offline and validate the whole export before changing anything.
  Invalid files, cancellation, and write failures leave saved chats intact.
  Unsaved matching messages must be saved first; damaged transcripts stay protected.
- Messenger saves separate conversations for each saved fursona and contact.
  After a temporary write failure, **Retry saving** saves the current conversation
  without clearing it, even offline. Sending another message also retries saving.
  Keep the window open until saving succeeds; unsaved messages exist only in memory.
  Unreadable existing transcripts stay protected from overwriting; retry saving
  is not offered for those files.
  Switching fursonas never loads another fursona's messages into the transcript
  or AI request, and delayed replies stay with the fursona that sent the message.
  Older contact-only chats are not loaded automatically. Select the contact and
  use **Preview older chat (read-only)…** to inspect it before choosing its owner.
  The preview is separate from the active conversation and never sent to AI.
  Cancel or close the preview to leave all files and ownership unchanged; continuing
  asks you to explicitly confirm the current fursona as owner. Assignment
  will not replace an existing conversation. The original bytes are retained
  in `Storage/UserData/Messenger/Legacy`, with an ownership record preventing
  assignment to another fursona. If assignment is interrupted, the same owner
  can retry; clearing its active chat does not delete the legacy backup.
- Every close Messenger contact has a distinct fictional shared history and
  friendship boundary with the active fursona. Memory details are selected
  repeatably from the saved fursona identity, displayed in Messenger, and
  included in each AI request. These private backstories do not replace public
  Directory biographies or give the 150 background members assumed friendships.
- The supplied 105-frame Windows startup animation plays at 20 frames per
  second, including three reverse/forward loop cycles; press Space to skip to
  login. The supplied startup sound plays when the desktop appears using
  Windows' built-in WAV playback
- A user-provided Windows 7 wallpaper is bundled with the app and scales to
  the desktop; missing or unreadable wallpaper files show an explicit error
- The supplied Start menu/taskbar bundle supplies the default `Background1`
  wallpaper, both Start button states, menu icons, task buttons, transition,
  and tray textures. The menu has the eight requested commands and a rotated,
  bold desktop account name. Programs expands into the installed local apps
  and a Windows Accessories submenu with Notepad, Calculator, Paint, and
  WordPad, Sticky Notes, Snipping Tool, and Windows Media Player. Paint opens
  and saves PNG/JPEG/BMP drawings. WordPad provides formatted editing with
  HTML, Markdown, and plain-text files. Sticky Notes save automatically per
  active fursona and are removed by Format and Reinstall. Snipping Tool captures
  a rectangular or full-screen image of the simulated Windows desktop, with
  copy-to-clipboard and PNG save. Windows Media Player scans `Storage/Media`
  for common audio/video formats and also adds files or folders directly to
  its current playlist. Named playlists can be saved, reopened, renamed, and
  deleted per fursona; missing files are reported when a playlist is opened
  and remain in the saved list. Playlist metadata is reset with user data,
  while media files are never copied or changed. Codec playback depends on the
  local Qt Multimedia backend. Recent Items remembers the last eight items opened or saved in
  Notepad, WordPad, Paint, or Snipping Tool.
  Windows Defender starts with each logged-in desktop session and is available
  from the notification-area shield and Accessories menu. Its quick/full scans,
  update check, and results are simulated; it never inspects or modifies files.
  Disk Defragmenter shows a full 80×44 colored block map that consolidates in
  one-to-five-block steps, most often one block at a time, then resets to a newly
  fragmented layout and repeats until stopped. It never accesses the actual drive.
  During either maintenance run,
  queued background and summary AI work temporarily takes priority over waiting
  direct chats, without interrupting active generation.
  The desktop's Screen Saver tab in Options offers full-screen Bubbles and
  Mystify animations, an idle timeout, and a preview; mouse or keyboard input
  returns to the desktop. The saved choice is user data and is cleared by
  Format and Reinstall.
  Search checks document names, and Run accepts `notepad(.exe)`,
  `calc(.exe)`/`calculator`, `mspaint(.exe)`/`paint`, `write(.exe)`/`wordpad`,
  `stikynot(.exe)`/`sticky notes`, `snippingtool(.exe)`, `wmplayer(.exe)`,
  `computer`, `directory`, and `messenger`. Help shows a clear unfinished-feature
  notice; Format and Reinstall remains available inside Options.
- The user-supplied Desktop ZIP provides six vertically arranged shortcuts:
  Recycle Bin, Desktop, Firefox, MSN Messenger, MushClient, and IRC Client.
  The welcome note is in the upper-right. Firefox opens the requested
  “Feature not implemented yet.” message; the other shortcuts open their programs.
  Double-clicking Desktop opens the supplied CD, DVD, floppy, external-drive, and
  internal-drive icons. Drive eject is simulated without changing archived files;
  drive format is unavailable.
- Recycle Bin shows the supplied empty/full artwork, changes to Full when a
  deleted item is stored, and opens a restore/empty window and right-click menu.
  Explorer moves personal Documents, Media, ROM, and removable-drive items into
  `Storage/UserData/Recycle Bin`. Restore chooses a non-overwriting name when a
  copy already exists. Empty and permanent delete require confirmation; Windows,
  model, profile, Messenger-history, and runtime folders are protected.
- Task buttons minimize/restore their windows and disappear when a window
  closes. Supplied navigation/hover/minimize/restore WAV sounds play on Windows.
  Log Off returns to user selection. MSN, network, local-LLM, MushClient, and
  mIRC activity icons share the tray area, with the clock separated from the icons.
- A confirmed format-and-reinstall action removes the local account and saved
  documents while preserving preinstalled programs and media, ROM, and model
  archives; restarting or entering Recovery Mode returns to boot and first-run
  setup. Recovery Mode from an ordinary shutdown asks for confirmation first.
- Account data and future media/model/ROM archives are stored locally in the
  Git-ignored `Storage/` directory

### Centralized local AI options

**Protected local servers:** Use **API key…** beside the main server or a role
address to save, replace, or remove a Bearer API key. Keys are stored in the
current Windows user's **Windows Credential Manager** (generic credentials under
`win7-2011/local-ai/`), never in `ai.json` or backend profiles. Existing saved
values are never displayed. Saving/removing a key takes effect immediately,
even before Apply; Cancel leaves it unchanged. Then use **Apply & Connect**, or
test the saved connection, to verify access. Blank role addresses inherit the
main address and its key. Different addresses/backends have independent keys;
roles using the same backend/address share one key. Removing a key returns that
endpoint to unauthenticated requests. Machine-level keys survive simulated
Format and Reinstall.

HTTP 401/403 failures identify authentication or permission problems without
showing the key or server error body. Requests never follow redirects; enter
the final local address instead. Private-network HTTP is unencrypted, so use
HTTPS outside loopback. No insecure credential-file fallback is provided:
non-Windows development hosts can still use unauthenticated endpoints, but
saving/removing keys requires Windows. These are credentials for your own local
desktop servers, not workspace/cloud integration credentials; any workspace
service credentials belong in Replit Secrets, never chat or tracked files.

Open **Start → Options → AI / Local Models**, or use **Open AI Settings** in
Messenger. The app uses llama.cpp (`llama-server`) for local models. Select the
server executable and a local GGUF file to let the app start and stop its own
server, or connect to a llama-server you started separately.

Messenger sizes recent model input separately from the full saved transcript.
llama-server uses `/props`'s active per-slot
`default_generation_settings.n_ctx` only for a single advertised model, not a
training window or a multi-model router's global properties. Metadata is optional:
missing, invalid or inaccessible metadata never blocks an otherwise available model.

Use Messenger's **Manual model window (tokens)** for a known server limit or a
smaller window. Limits of at least 256 tokens are saved separately by backend,
server address and exact model name; zero removes the override. A manual limit
cannot increase a provider-reported window. Applying model settings retains these
limits. Input reserves up to 512 tokens (one quarter for very small windows) for
the reply, and requests cap output with `num_predict` / `max_tokens`.
The remaining input allowance uses a conservative UTF-8 byte estimate, including
persona instructions and estimated chat framing. It is **not an exact token
count or a fit guarantee**. The adjustable **AI input budget (bytes)** can reduce
the allowance further. Unknown windows retain an 8192-byte default and clearly
show that total fit is unknown; lower the budget after a server rejection.
Changing a limit never sends or retries a message. Older messages omitted from
model input remain available for viewing, saving and export.

Use **Pinned details / optional summary…** in Messenger to keep selected older
details in AI input. Paste or edit pins, and review the exact additional text
before **Save context**. Pins and approved summaries are saved separately for
each fursona/contact and included in the same input allowance; oversized notes
are rejected rather than silently shortened. Remove either field and save to
stop using it. Clearing a conversation also clears its notes.

**Request optional summary** uses the assigned **Summaries and memory** model.
The dialog shows the bounded excerpt of omitted older messages being submitted,
including which earlier messages will not be summarized. It does not claim to
summarize the whole transcript. Generated text is only a draft: review/edit it
and save explicitly to use it in direct chat. An unavailable model, empty reply,
failed request or cancellation leaves existing notes and the transcript unchanged;
bounded direct chat does not require a summary model and failed sends are never
automatically retried. Separate notes are **not included in transcript exports**.

1. Before making a standalone Windows copy, prepare the pinned runtime from the
   workspace root:

   ```powershell
   py -3.13 win7_2011\package_llama_runtime.py
   ```

   This packaging-only command downloads the official llama.cpp **b11563**
   Windows x64 CUDA 12.4 server archive and its matching CUDA DLL archive,
   verifies each pinned SHA-256 and file size, then writes the verified server
   and DLLs to `win7_2011/Storage/Runtime/llama.cpp/`. The two downloads total
   about 626 MiB. The folder is under ignored `Storage/`, so it is not added to
   ordinary Git history. When preparing the standalone Windows copy, include
   this generated runtime folder beside the app; do not expect a fresh checkout
   or the running app to download it. The model remains a separate local file
   and is not bundled.

   The matching bundle includes `llama-server.exe`, `ggml-cuda.dll`,
   `cublas64_12.dll`, `cublasLt64_12.dll`, `cudart64_12.dll`, and all other
   DLLs from both verified upstream archives beside the executable, plus
   upstream license files and a checksum manifest. Keep the complete DLL set
   together. An NVIDIA display driver is still required on the target PC.

   CUDA 12.4 is selected for the GTX 1080 Ti (Pascal, compute capability 6.1):
   the upstream CUDA build configuration includes `61-virtual` for CUDA
   toolkits below version 13, allowing the installed NVIDIA driver to JIT the
   Pascal kernels. Do not substitute the CUDA 13 build; NVIDIA documents that
   CUDA 13 removes offline compilation support for architectures below 7.5.
   This selection is based on the upstream release and build configuration,
   not a claim that the runtime has already been exercised on the target PC.
   See the [b11563 release assets](https://github.com/ggml-org/llama.cpp/releases/tag/b11563),
   [upstream Windows CUDA build workflow](https://github.com/ggml-org/llama.cpp/blob/b11563/.github/workflows/build-cuda-windows.yml),
   and [CUDA architecture defaults](https://github.com/ggml-org/llama.cpp/blob/b11563/ggml/src/ggml-cuda/CMakeLists.txt).

   Windows validation has been confirmed on the target PC for NemoMix Direct
   Conversations, the other configured roles, and the app-managed server's
   startup, shutdown, and restart. This Linux workspace did not independently
   run those Windows checks. For future hardware or runtime changes, repeat the
   following device-specific checks:
   - Confirm `nvidia-smi` identifies the GTX 1080 Ti and
     `llama-server.exe --version` starts without a missing-DLL error.
   - In **AI / Local Models**, choose the bundled executable and an existing
     chat-capable GGUF. Set GPU layers to a suitable value, then **Apply &
     Connect**. Confirm the app-managed process appears and the loaded model
     appears in **Refresh models**.
   - Send a short real chat request and confirm the server log reports CUDA
     offload (not CPU-only fallback).
   - Close the simulated desktop normally; confirm its app-managed
     `llama-server.exe` process exits. Reopen and repeat once to check a clean
     restart.

2. In **AI / Local Models**, select the app-managed `llama-server.exe` and an
   existing GGUF, then keep the address on loopback (the default is
   `http://127.0.0.1:9931`). The app launches the process only when that address
   is unavailable, waits while the model loads, and stops its own process when
   the Windows desktop session ends. It never downloads a server or model.
    If no model file is configured and `Storage/Models` contains exactly one
    `.gguf`, the app selects it automatically and uses its filename as the
    Direct conversations model name. With multiple GGUF files, choose the file
    and model name explicitly in Options.
    The published `NemoMix-Unleashed-12B-*.gguf` files lack an embedded chat
    template. For those filenames, the managed server explicitly uses
    `mistral-v3-tekken` and the model author's recommended DRY repetition
    control (`--dry-multiplier 0.8`), rather than llama.cpp's ChatML fallback.
    Other models retain their own embedded templates. Fully close and restart
    the simulator after updating these launch options; an already-running
    external server must be configured and restarted separately.
   Root addresses and addresses ending in `/v1` are accepted for externally
   managed llama-server endpoints, including an API prefix.
3. You can also start `llama-server.exe` yourself with an existing GGUF. If the
   configured endpoint already responds, the simulator uses it without starting
   a second process.
4. Use **Test saved connection / Refresh models** to discover loaded models
   at the saved address. For a changed address, use **Apply & Connect**.
5. Choose a model for Direct Conversations, Background Community Activity,
   and Summaries and Memory, then click **Apply & Connect**. All roles can use
   the same model; blank assignments remain unavailable. Optional **Server for
   this role** addresses let separate llama-server instances serve different
   models. Leave these blank to use the main address.
6. The Activity tab shows real engine status, queued work, and assignments.
   **Cancel model work** cancels pending/running requests. Settings cannot be
   changed while model work is active. The simulator refreshes saved server
   addresses once after each successful desktop login; it does not poll in the
   background. After restarting a local server during a session, use **Reconnect
   saved servers** here to refresh availability without editing settings. It uses
   saved addresses, not unsaved Options edits, and is available only when model
   work is idle. Failed or cancelled messages are never resent: send a new
   message yourself when ready. Reconnecting does not end simulated internet
   outages. **Test saved connection / Refresh models** still works.

Older centralized AI settings are migrated once to the llama.cpp format. If an
older installation has only `Storage/System/ollama.json`, its saved model name
is copied to all three roles and the app uses the default llama-server address;
choose a GGUF and confirm the exact advertised model ID in **AI / Local Models**.
The original `ollama.json` is retained unchanged as a backup and is not used to
connect. The migration does not alter Messenger histories. Applying settings
atomically writes `Storage/System/ai.json`. AI settings survive Format and
Reinstall because they describe the local machine, not a fursona.

One shared service runs at most one generation at a time. Direct conversations
take priority over queued summaries and background jobs. Background jobs wait
during simulated slowdowns/outages, and direct conversations are cancelled
during a simulated disconnection. Actual model availability remains distinct
from fictional internet status. Models are never downloaded by the simulator.
A server manually started by the user manages its own lifetime; an app-managed
llama-server is loaded on demand and stopped when the desktop session ends.

llama-server discovery uses `GET /v1/models`; chat uses
`POST /v1/chat/completions` with `stream: false`. Use the exact advertised model
ID or `--alias`, not a guessed GGUF filename. A normal single-model server lists
its loaded model only, not every unloaded GGUF in `Storage/Models`. A separately
configured llama-server router may advertise multiple models and load them
according to its own configuration. The simulator does not call model-management
endpoints. Dropdowns show only models discovered at that role's saved endpoint;
refresh reports errors per endpoint without disabling roles on healthy servers.
Cancellation aborts the HTTP request and discards its result; server-side cleanup
depends on the server honoring a disconnected client. Optional API keys for
protected local servers can be entered with **Set API key**; they are stored in
Windows Credential Manager, not in `ai.json`.

Developer-only opt-in checks for actual llama-server model unloading and
explicit reconnect are documented in
[`tests/REAL_AI_TESTS.md`](tests/REAL_AI_TESTS.md). They manage only disposable
test aliases or caller-owned router presets; ordinary tests remain offline.

This is the foundation, not the full social world yet: other communication
services, media/TV library,
productivity suite, games, and additional preinstalled programs remain future
slices. Messenger never substitutes scripted text for model replies.

To chat, open Windows Live Messenger and select **Open AI Settings**. Set the
direct-conversation model and choose **Apply & Connect**. Settings are saved in
`Storage/System/ai.json`; older settings are migrated once as described above.
Only localhost and private/local-network endpoints are
accepted. Simulated service interruptions pause online messaging and background
work while local programs remain available; timers stop when the desktop shuts
down.

For UI testing, set `WIN7_SIM_FAST_BOOT=1` before launching to play only the
initial animation pass at a faster rate. Normal startup holds the BIOS screen
for about 6.7 seconds so the POST beep and memory-test result line up, then
  follows the supplied three-cycle Windows animation timing (about 18.45 seconds).

## Local data layout

`Storage/System/account.json` stores the local account and fursona profile
metadata; `Storage/System/ai.json` stores the shared local engine, model-role
assignments, and app-managed llama.cpp launch settings. An older
`Storage/System/ollama.json` is retained unchanged after its one-time model
assignment migration; it is no longer read after `ai.json` is created and is
never a server connection source.
`Storage/Profiles` and `Storage/UserData/Documents` hold user profile
files and documents. The application creates missing folders without deleting
existing data. Format-and-reinstall clears only those user-owned locations and
the account file; it leaves `Storage/Media`, `Storage/ROMs`,
`Storage/Models`, and `Storage/Runtime` intact.

## Authenticity notes

See `research/asset-register.md` for the sources behind the 2011 motherboard,
AMI firmware, BIOS release, Windows startup references, and user-provided
imagery and sounds. The wallpaper, boot animation frames, BIOS logos, POST
sound, Windows startup sound, login artwork, and shutdown imagery and sound are
bundled from user-provided assets; screen text and shutdown transitions are
rendered by the app. The register distinguishes these from sourced historical
facts.
