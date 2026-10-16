# llama-server API reference

Researched against the upstream server documentation on 2026-10-12:
https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md

- `GET /v1/models` returns OpenAI-style `data` entries with exact `id` values.
  Single-model mode reports the loaded model; by default its ID is the model
  path, or the alias supplied via `--alias`. This is not a disk inventory.
- `POST /v1/chat/completions` accepts `model`, `messages`, and `stream`.
  Non-streaming replies contain `choices[0].message.content`. Reasoning-only
  and tool-only responses must not be substituted for visible chat text.
- `/health` reports 503 while loading. API errors contain `error.message`;
  protected servers can report authentication errors. The adapter reports
  these and malformed replies, rather than substituting simulated replies.
- Current router mode can advertise multiple configured models, but support
  for a router is not assumed. Independent role endpoints work with ordinary
  single-model servers. No scanning, downloading, model-management calls, or
  executable launch is performed by the simulator.
- Current documented default port is 9931; users of older builds may need
  8080 or their explicitly configured port. Connection settings are editable.
- Native Qt request abort is the cancellation mechanism. The local service
  retains one generation request at a time and suppresses cancelled results;
  actual server cleanup is subject to the server's disconnect handling.

This research informed the API contract; tests use local HTTP fixtures and do
not establish hardware performance or the suitability of a particular GGUF.
