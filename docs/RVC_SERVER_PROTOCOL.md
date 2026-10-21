# Voice-conversion server protocol

The `rvc-http` adapter talks to a local HTTP service so the heavy RVC runtime
can live in its own Python environment (upstream RVC needs a specific
toolchain; see [AI_HANDBOOK.md](AI_HANDBOOK.md) section 4). This file is the
contract both sides implement.

## Endpoints

### GET `/health`

Response: `200 application/json`

```json
{"engine": "rvc", "ready": true}
```

`ready` is `true` when the `rvc-hub` engine (`huggingface-hub-rvc`) is installed;
otherwise conversion returns `500` with installation instructions.

### POST `/convert`

Request:

- body: WAV bytes (any sample rate; mono or stereo)
- `Content-Type: audio/wav`
- `X-Voice-Model`: display name (informational)
- `X-Model-Path`: absolute path to the `.pth` checkpoint
- `X-Index`: absolute path to the `.index` file, or empty

Response on success: `200 audio/wav`, float32 mono at 40 kHz.

Errors: `4xx/5xx application/json` with `{"error": "human readable message"}`.

## Implementations

- Reference server: `vivoice serve` (see `src/vivoice/server.py`); conversion
  runs through the `rvc-hub` engine and requires `uv sync --extra ai`.
- Client: `src/vivoice/ai/rvc/http.py` (`engine: rvc-http`).

The client maps HTTP errors to `ConversionError`, timeouts to a reachability
message, and non-WAV payloads to a decoding error. Payloads are capped at
128 MB on the server side.
