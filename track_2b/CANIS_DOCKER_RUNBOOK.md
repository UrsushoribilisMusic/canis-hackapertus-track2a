# Canis Docker Runbook

This directory is the HackApertus Track 2B Docker target for Canis.

## Prerequisites

- Docker or OrbStack running.
- Hugging Face access to `swiss-ai/Apertus-v1.5-8B`.
- `HF_TOKEN` exported in the shell for first-time model access.
- The Hugging Face cache available at `~/.cache/huggingface`.

## Fast UI/API Smoke Test

This starts the Dockerized Canis web app with the deterministic mock runtime.
It is fast and useful for checking the UI, routes, and API contract.

```bash
cd track_2b
make run
```

Open:

```text
http://127.0.0.1:8080/
```

## Real Apertus 8B Runtime

This starts the same web app backed by `swiss-ai/Apertus-v1.5-8B` through
Swiss AI's pinned Transformers branch.

```bash
cd track_2b
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
make run-model
```

If `make run` is already serving the fast mock container, stop it with `Ctrl-C`
before starting `make run-model`.

The default real-model run uses:

- `CANIS_ENABLE_MODEL=1`
- `CANIS_MODEL_ID=swiss-ai/Apertus-v1.5-8B`
- `CANIS_MAX_NEW_TOKENS=32`
- host cache mounted from `${HF_CACHE:-~/.cache/huggingface}`

Use an explicit cache path when the model files live somewhere else:

```bash
HF_CACHE=/path/to/huggingface-cache make run-model
```

If the mounted cache does not contain Apertus yet, Transformers will download
the full gated model into that cache before the first answer.

When the real model is running, the browser UI shows a live waiting panel with
elapsed seconds, pipeline steps, and a moving scan bar. On good hardware a
question may take about a minute; on CPU or offload-heavy Docker runs, our tests
have taken several minutes for one question.

Override the token cap when needed:

```bash
CANIS_MAX_NEW_TOKENS=8 make run-model
```

## Health Checks

```bash
curl -sS http://127.0.0.1:8080/api/health
curl -sS http://127.0.0.1:8080/api/models
```

Expected real-model health after the first successful chat request:

```json
{"ok":true,"model":"swiss-ai/Apertus-v1.5-8B","runtime":"transformers","model_loaded":true}
```

## Known Latency

The Docker path currently uses PyTorch/Transformers with CPU/disk offload.
The model loads successfully, but autoregressive generation is slow on the
Mac Mini Docker runtime. A measured local run produced 8 tokens in about 79s.

The iOS/MLX path is expected to be much faster on Apple hardware. For the
HackApertus Docker target, keep prompts short and keep `CANIS_MAX_NEW_TOKENS`
low unless a long wait is acceptable.

## Current Readout Status

The backend generates answers with Apertus 8B in real-model mode. After
generation, Canis attempts a hidden-state forward-lens readout using the compact
directions artifact bundled in `src/backend/canis_disposition/artifacts/`. If
the active Transformers model does not expose hidden states/logits, the backend
logs the issue and falls back to the lexical readout.

## Useful Commands

```bash
docker ps
docker logs --tail 120 canis-track2b
docker stop canis-track2b
make test
make probe-model
```
