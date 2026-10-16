# Real local-model checks (opt-in)

**Ollama is no longer an application backend.** Historical Ollama results are
retained in `REAL_AI_RESULTS.md`; the opt-in tests documented here cover
llama-server only.

The active tests use the production Qt client and `AIService`/`AIChannel` with
**real HTTP responses** from your server. Request recording only observes calls;
it does not fake responses. No executable detection, server startup, or network
requests happen unless you explicitly enable a supported llama-server check.

## Versions and limitations

| Provider | Confirmed version / supported API baseline | What is required |
| --- | --- | --- |
| Ollama (historical only) | **0.6.8 passed live** before app support was retired | `/api/version`, `/api/tags`, `/api/copy`, `/api/delete`, `/api/generate`, `/api/ps`, `/api/chat` |
| llama.cpp llama-server | **b11563-a05e58c98 (0.6.0-dev) passed live**; v0.6.0 router API baseline | `/props` with router metadata/build info, `/v1/models` with `status.value`, `/models/load`, `/models/unload`, `/v1/chat/completions` |

These baselines were checked against the upstream versioned server source:
[Ollama v0.6.8 routes](https://github.com/ollama/ollama/blob/v0.6.8/server/routes.go)
and [llama.cpp v0.6.0 router](https://github.com/ggml-org/llama.cpp/blob/v0.6.0/tools/server/server-models.cpp).
The two bold versions above were executed successfully with temporary isolated
Linux CPU servers and a small chat GGUF; see [REAL_AI_RESULTS.md](REAL_AI_RESULTS.md)
for retained results. Other builds are compatibility targets, **not a claim
that every version was executed here**. A real run prints the exact Ollama
version or llama-server build; retain that output with the test result when
certifying an installation. An enabled but incompatible/unreachable server
fails the test; it is not silently skipped. The temporary servers are not
permanently installed or needed by ordinary tests.

Older single-model llama-server installations have no independent per-model
unload operation while keeping the endpoint alive. Stopping the whole process
is an endpoint outage, not this scenario. Use the separate offline
`test_ai_reconnect.py` for endpoint restart coverage. This suite intentionally
requires the router API rather than pretending single-model servers support it.

The unloaded-model suite above uses a dedicated **unauthenticated local/private test endpoint**, not a production
server. API keys are not read by this suite; it injects an empty credential
resolver instead of accessing Windows Credential Manager. URLs containing
credentials, public hosts, and redirects are rejected.

## Model-limit verification (Windows only, separate opt-in)

**Status: prepared, not certified on Windows.** The earlier Linux recovery
results do not verify model sizing or native Windows controls. The
`RealModelLimitTests` below is independent of unload/reconnect and authentication
checks. It neither touches credentials nor exercises exports/reinstallation.
Run it with the recovery/auth flags unset, against dedicated, unauthenticated
loopback servers. Reserve the sources and servers exclusively for testing.
Enabled runs fail (rather than skip) off Windows, without the ownership
acknowledgement, or without `QT_QPA_PLATFORM=windows`.

Use a chat-capable small-weight model supporting **8192 tokens or more**.
"Small" and "large" below mean **4096- and 8192-token runtime windows**, not
different parameter counts: sharing a GGUF keeps this check practical on CPU.
4096 leaves room for the real contact/profile instructions and some history.
Do not use the recovery suite's 2048-token setup for this check.
The test never downloads weights, starts/stops servers, or changes server flags.

### llama-server: two disposable single-model configurations

Use two reserved processes, not the recovery router. Router-global `/props`
cannot establish an arbitrary model's runtime context; the client deliberately
does not assign that metadata to multiple advertised IDs. Both processes may
use the same existing chat GGUF, but each must advertise exactly one distinct
alias. Nothing in this check loads/unloads a router preset or deletes a file.

Start each command in its own terminal (replace the GGUF path):

```powershell
llama-server.exe -m C:\Models\chat.gguf --alias win7-limit-small --ctx-size 4096 --parallel 1 --threads 2 --n-gpu-layers 0 --host 127.0.0.1 --port 29931
llama-server.exe -m C:\Models\chat.gguf --alias win7-limit-large --ctx-size 8192 --parallel 1 --threads 2 --n-gpu-layers 0 --host 127.0.0.1 --port 29932
```

Then in a third terminal:

```powershell
$env:QT_QPA_PLATFORM = "windows"
$env:WIN7_REAL_LIMIT_TEST_OWNED = "YES"
$env:WIN7_REAL_LIMIT_LLAMA = "1"
$env:WIN7_REAL_LIMIT_LLAMA_SMALL_URL = "http://127.0.0.1:29931"
$env:WIN7_REAL_LIMIT_LLAMA_LARGE_URL = "http://127.0.0.1:29932"
$env:WIN7_REAL_LIMIT_LLAMA_SMALL_MODEL = "win7-limit-small"
$env:WIN7_REAL_LIMIT_LLAMA_LARGE_MODEL = "win7-limit-large"
python -m unittest win7_2011.tests.test_ai_real_servers.RealModelLimitTests.test_llama_model_limits_windows -v
```

`--parallel 1` matters: verify the **per-slot** runtime window in
`/props.default_generation_settings.n_ctx`, not `n_ctx_train` or a total shared
context. Both the direct preflight and production Qt discovery must report the
expected 4096/8192 values. `/v1/chat/completions` must receive `max_tokens`
matching the reserve; `usage.completion_tokens` must be positive and not exceed
it. Missing metadata/usage, incompatible APIs and unreachable servers fail this
enabled certification; the application itself still supports unknown metadata
using its adjustable byte estimate. Retain `llama-server.exe --version` if the
build does not expose `build_info` in `/props`.

### What the automated sizing checks assert

The active llama-server test uses the real `MessengerApp`, `AIService`, client,
persona instructions and synthetic long history. Settings/history are patched to
a temporary directory, never the user's `Storage` directory.

1. Provider discovery updates Messenger's input budget to window minus reply
   reserve. Model requests preserve the system prompt and newest user message,
   omit only whole old messages, and fit the conservative UTF-8 byte estimate.
2. One explicit Send creates exactly one generation; the actual response
   reports output usage within the request cap. This is **not exact tokenizer
   verification**, nor a guarantee every arbitrary chat template will fit.
3. Saving a **3072-token manual model limit** through the spinbox save handler
   produces no chat, saves the per-endpoint/model setting, and reduces the input
   budget to **2560 bytes** while reserving **512 reply tokens**.
4. A fresh Python interpreter loads that persisted limit from disk. Recreating
   the service and Messenger reloads it and the full saved history without
   replay; only a new explicit send generates. This tests disk persistence and
   application-object restart, not human close/relaunch interaction.
5. Switching to the large model performs discovery only, resets the manual
   control to automatic, and expands the input budget to **7680 bytes**.
   The next explicit send includes more recent history than the small-window
   send. Switching back restores the small model's own saved 3072 limit,
   without a chat until Send is clicked again.
6. All original synthetic messages remain saved, with exactly one new user
   message and one genuine assistant reply per click. Source models/files are
   untouched; router presets are restored to their initial loaded states.

### Native Windows controls and full application restart

The automation invokes widgets programmatically using Qt's Windows plugin.
It does **not** certify real keyboard/focus behavior, layout or manual
close/relaunch. Complete this additional checklist on a disposable desktop
installation with the same two test configurations before marking the Windows
verification passed:

- Launch the simulator normally. In Options → AI / Local Models assign the
  small model to direct conversation, Apply, and open Messenger.
- Confirm the status identifies the 4096-token provider window and 512-token
  reply reserve. Enter enough synthetic exchanges to omit older context;
  send a new message and check the older transcript remains visible.
- Type **3072** into the manual model-window control and move focus away.
  Confirm it says manual limit and the input budget becomes **2560**. Editing
  this control must not send a chat. Also type an invalid **1**, leave the
  field, and confirm the error is visible and the saved 3072 limit remains.
- Close the simulator normally, relaunch the same disposable installation,
  select the same profile/contact, and confirm manual **3072**, budget **2560**,
  and the complete transcript. Relaunch must not send a chat by itself.
  Click Send with a new message and confirm exactly one reply arrives.
- In Options switch to the large configuration, Apply, and confirm automatic
  **8192**, budget **7680**, and reserve **512**. Apply alone must not generate.
  Send a new message; switch back and confirm manual **3072** is restored;
  only another deliberate Send may generate.
- Check the manual-limit and byte-budget fields, omission status and Send
  button are readable, focusable and not clipped at your Windows display
  scaling. Keep actual prompts/transcripts out of retained results.

Retain the standard test output, Windows version/display scaling, provider
versions, GGUF/model identifier, windows used, manual checklist pass/fail and
cleanup outcome in `REAL_AI_RESULTS.md`. Record failures or not-run items
explicitly. Do not replace the previous Linux recovery evidence with Windows
sizing claims. Stop only your dedicated processes and remove only caller-created
test sources/configurations when you no longer need them; no bulk model deletion.

## Separate authenticated recovery check (Windows only)

`test_ai_real_auth.py` is independent of the unloaded-model suite and its flags.
It uses the production `WindowsCredentialStore`, not an empty resolver or an
in-memory substitute. Native Windows execution against a protected server has
**not been verified in the Linux workspace**. Offline fixture execution of the
same scenario is not native/live certification.

Reserve **two distinct caller-owned local/private endpoints**, with installed,
chat-capable models. Neither endpoint may be in use by another desktop session
or workload during this test. The test temporarily replaces the primary
endpoint's saved credential with a random invalid key, then restores it. It
does not start/stop servers, alter server auth policy, pull/unload/delete models,
or change connection settings files. Normal cleanup restores the original key
even on assertion failures or partial writes. Forced termination cannot run
cleanup; re-enter your valid key in Options if interrupted. Keep your valid key
available in your own secure password manager.

Supported targets:

- Authenticated llama-server: `/v1/models` and `/v1/chat/completions` must require
  the same bearer key and reject a wrong key with HTTP **401 or 403**. A router is
  not required; single-model servers are supported.
Use a different endpoint for the healthy background role, protected by its own
valid saved credential; it can expose the same model ID. Supply the exact model
IDs advertised by each endpoint. Optional metadata (`/props` for llama-server)
is queried by normal discovery; missing metadata is not an authentication
certification of that route.

Before running, use the desktop's Options → AI / Local Models API-key dialogs
to save both keys for the selected backend and exact endpoint URLs. You can
select each endpoint in the URL field and save its key **without Apply**.
Keys are stored under that Windows account in Windows Credential Manager.
Do not put keys in environment variables, command arguments, URLs, configuration
files, transcripts, screenshots, or test output. Do not run with HTTP debug
logging, traceback-local capture (`pytest --showlocals`), debugger dumps, or
unredacted server/proxy access logging. Configure your caller-owned servers to
keep authorization headers and keys out of their logs.

All variables below are **non-secret** configuration:

```powershell
$env:WIN7_REAL_AUTH = "1"
$env:WIN7_REAL_AUTH_TEST_OWNED = "YES"
$env:WIN7_REAL_AUTH_BACKEND = "llama_cpp"
$env:WIN7_REAL_AUTH_URL = "http://127.0.0.1:9931"
$env:WIN7_REAL_AUTH_MODEL = "chat"
$env:WIN7_REAL_AUTH_HEALTHY_URL = "http://127.0.0.1:9932"
$env:WIN7_REAL_AUTH_HEALTHY_MODEL = "chat"
python -m unittest win7_2011.tests.test_ai_real_auth -v
```

The enabled check fails rather than skips if run off Windows, if configuration
is missing/unsafe, or if a key/server/model is unavailable. With the flag unset,
it skips before creating a Qt application, reading credentials, or networking.
Both endpoints and the ownership acknowledgement are mandatory; there is no
partial "healthy endpoint not run" path.

Assertions cover successful discovery/generation at both endpoints; a cached
primary connection rejecting an invalid saved key; endpoint-specific (not
model-specific) invalidation; queued primary work rejected without transmission;
queued and fresh healthy-role work still generating; protected discovery also
rejecting the invalid key; changing the saved key via `AIService.update_api_key`
without implicitly restoring availability; and explicit reconnect performing
discovery/optional metadata only. Reconnect never resends either rejected
message, and only a newly submitted message generates afterward. The healthy
credential remains unchanged. This invalid-key scenario does **not** rotate or
revoke the server's own accepted key and does not certify external revocation
administration.

Retain only the standard unittest result, Windows version, provider/proxy
version, and whether the required two endpoints were used. Do not attach keys,
credential dumps, payloads, or private server responses. Live/native results
must be recorded separately from the unauthenticated Linux results in
`REAL_AI_RESULTS.md`.

## llama-server: caller-owned presets, no file deletion

Prepare an isolated router with **test-owned** preset names beginning
`win7-recovery-test-`. A preset can refer to your existing chat GGUF, but the
router and preset lifecycle must be reserved for this test. The suite does not
create/delete presets, download GGUFs, delete GGUFs, or kill processes.

For compatible builds, an example preset file is:

```ini
[win7-recovery-test-primary]
model = C:\Models\small-chat.gguf
ctx-size = 2048

[win7-recovery-test-healthy]
model = C:\Models\small-chat.gguf
ctx-size = 2048
```

Start your router yourself (without a top-level `-m`):

```powershell
llama-server.exe --models-preset C:\Tests\recovery.ini --no-models-autoload --models-max 2 --host 127.0.0.1 --port 9931
```

Then, in another terminal:

```powershell
$env:WIN7_REAL_LLAMA = "1"
$env:WIN7_REAL_LLAMA_TEST_OWNED = "YES"
$env:WIN7_REAL_LLAMA_URL = "http://127.0.0.1:9931"
$env:WIN7_REAL_LLAMA_PRIMARY = "win7-recovery-test-primary"
$env:WIN7_REAL_LLAMA_HEALTHY = "win7-recovery-test-healthy"
python -m unittest win7_2011.tests.test_ai_real_servers.RealServerTests.test_llama_router_unload_and_reconnect -v
```

The acknowledgement is mandatory; prefix naming alone does not imply ownership.
`/props` must report `role: router` and `models_autoload: false`. Use at least two
model slots and enough RAM for the two loaded presets. Their exact IDs must
already appear in `/v1/models`; an arbitrary GGUF filename is not a model ID.
The runner snapshots their initial loaded/unloaded states and restores those
states during cleanup, waiting for server transitions to finish.

The test loads the preset(s), discovers them through the real client, generates,
unloads only the primary, and verifies its actual chat error is classified as
model-specific rather than invalidating the endpoint. It then checks queued-job
isolation and explicit-reconnect/no-replay guarantees.
The router may still **advertise** an unloaded preset; the failed generation,
not disappearance from discovery, proves its unavailability.

If your isolated router supports only one loaded model, omit
`WIN7_REAL_LLAMA_HEALTHY`. Discovery, unload, model-specific failure, reload,
and reconnect still run; the output explicitly says the same-endpoint
healthy-model check **NOT RUN**. Do not count that as a full two-model result.

On interruption/forced termination Python cleanup cannot be guaranteed. For a
llama-server router, restore only your dedicated test presets' previous states.
Never bulk-delete model names or a model directory.

## Offline/default runs

From the repository root, leave all opt-in flags unset:

```powershell
Remove-Item Env:WIN7_REAL_LLAMA -ErrorAction SilentlyContinue
Remove-Item Env:WIN7_REAL_AUTH -ErrorAction SilentlyContinue
Remove-Item Env:WIN7_REAL_LIMIT_LLAMA -ErrorAction SilentlyContinue
python -m unittest discover -s win7_2011/tests -v
```

All current opt-in llama-server and authentication checks report `skipped`; the
fixture tests and offline safety checks still run. Merely setting a URL or
installing a server does not enable these tests. In a POSIX shell, use
`export NAME=value` instead of PowerShell's `$env:NAME = "value"` syntax. Each
network/generation/transition wait has a 180-second limit. Unexpected error
shapes fail with the real client's category and availability assertions; there
is no automatic retry of chat work.
