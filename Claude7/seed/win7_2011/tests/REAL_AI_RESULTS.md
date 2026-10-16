# Real-server recovery verification

Verified on 2026-10-12 using official Linux x86-64 CPU binaries, isolated loopback
ports and model storage under the ignored `generated-artifacts/real-ai/`
directory. These were actual server processes, not the HTTP fixture handlers.
No user installation, existing model directory, or Windows credentials were used.

## Test model and server setup

- Chat GGUF: `bartowski/SmolLM2-135M-Instruct-GGUF`,
  `SmolLM2-135M-Instruct-Q4_K_M.gguf`.
- Ollama **0.6.8**, official `ollama-linux-amd64.tgz`; isolated
  `OLLAMA_HOST=127.0.0.1:21434`, test-only `OLLAMA_MODELS` and `HOME`.
  A test setup source alias was created by importing the GGUF with a Modelfile
  (`num_predict 16`, `num_ctx 2048`, `num_thread 2`). The integration case copied
  this source into its two disposable UUID aliases.
- llama-server **0.6.0-dev, build 11563, commit a05e58c98**; official
  `llama-b11563-bin-ubuntu-x64.tar.gz`. Router on port 29931 with
  `--no-models-autoload --models-max 2`. Two test-only presets pointed at the
  same GGUF with separate loaded subprocesses, `ctx-size=2048`, `threads=2`,
  and `n-gpu-layers=0`. `/props` reported `build_info=b11563-a05e58c98`.

## Retained unittest output

Environment variables and commands match [REAL_AI_TESTS.md](REAL_AI_TESTS.md)
with the isolated ports/source described above.

```text
test_llama_router_unload_and_reconnect ... 
Real llama-server build: b11563-a05e58c98
ok

Ran 1 test in 38.295s
OK
```

```text
test_ollama_unload_autoload_then_remove_and_reconnect ...
Real Ollama server version: 0.6.8
Test-owned aliases: win7-recovery-test-80f61d62880f4ca0982ee4b9098efd8f-primary:latest, win7-recovery-test-80f61d62880f4ca0982ee4b9098efd8f-healthy:latest
ok

Ran 1 test in 3.253s
OK
```

Both cases ran the healthy second model at the **same endpoint**; neither used
the one-model omission path. Assertions confirmed real discovery/generation,
model-specific unavailability rather than an endpoint outage, queued-job
rejection without another chat request, explicit reconnect with discovery only,
no replay of failed/queued messages, and successful generation only for a new
send. Ollama also passed memory unload followed by automatic reload before its
separate disposable-alias removal scenario.

After both cases, direct server checks confirmed:

- Ollama `/api/tags` contained only the test setup source; both disposable run
  aliases were removed by cleanup.
- llama-server `/v1/models` reported both test presets `unloaded`, matching their
  initial states. No model/preset/GGUF deletion was performed by this case.

The temporary server processes were stopped after verification. Downloaded
archives/weights/runtime files are ignored test outputs, not application
dependencies or files committed to the repository.

## Offline checks

The full desktop offline unittest suite passed. The final focused guardrail run
passed all 12 safety cases with both opt-in integration cases skipped when their
flags were unset. Installing or running a server does not itself enable these
checks. No Windows execution or authenticated-server result is claimed here.

## Authenticated check readiness (not a live result)

The separate `test_ai_real_auth.py` scenario is implemented for caller-owned
protected endpoints and Windows Credential Manager. Its complete flow passed
offline HTTP fixtures for both `llama_cpp` and `ollama`, including restoration
after a simulated partial credential write. Safety tests cover the disabled
no-access path, explicit non-Windows failure, ownership acknowledgement, and
unsafe/identical endpoint rejection. These fixtures do not certify a real
authentication proxy or the native Windows credential API.

No caller-owned protected Windows endpoints were available in this workspace.
The real authenticated case therefore remains opt-in and unexecuted here.
Follow [REAL_AI_TESTS.md](REAL_AI_TESTS.md) on the target Windows desktop and
retain its standard unittest result plus the provider/proxy and Windows versions
before claiming native/live authentication recovery.

## Model-limit Windows check readiness (not a live result)

The user requested that the remaining live Windows runs and native-controls
checklist be ignored for now. They are deferred, not passed; retain the prepared
tests and setup instructions for when the user revisits Windows verification.

The separate `RealModelLimitTests` scenarios target actual Windows Ollama and
two single-model llama-server processes with 4096/8192-token windows. They cover
metadata discovery, request context/output caps, per-model manual limits,
disk persistence in a fresh interpreter, service/Messenger recreation, explicit
sends after switching, and complete synthetic transcript preservation.
`REAL_AI_TESTS.md` includes disposable configurations and the separate native
keyboard/focus/full-relaunch checklist.

This workspace is Linux and has neither local server installed. No native
Windows sizing run or manual controls check has been performed here. The
automated harness can be checked over offline Qt HTTP fixtures, but those
results must not be counted as Windows or live-provider certification.

The focused Linux/offscreen check passed:

```text
python -m unittest win7_2011.tests.test_model_context win7_2011.tests.test_messenger_context win7_2011.tests.test_real_ai_safety win7_2011.tests.test_ai_real_servers -v
Ran 35 tests in 8.869s
OK (skipped=4)
```

This includes the shared sizing harness exercised with fixture responses for
both providers and the opt-in safety guards. The four skips are the two legacy
live recovery cases and the two new Windows sizing cases, with flags unset.
No production model-limit implementation was changed on the strength of these
fixture results.
