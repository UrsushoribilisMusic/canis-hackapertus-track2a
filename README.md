# Canis Apertus Lab — HackApertus Track 2B

Canis is a HackApertus Track 2B submission that makes Apertus answers more
inspectable. It returns the normal answer plus a compact disposition readout:
whether the model appears confident, unsure, curious, concerned, reluctant,
warm, or neutral.

The central idea is simple: open weights make new product signals possible.
Canis uses local model access to expose a model-state signal that closed hosted
APIs normally hide, while keeping prompts and user documents local.

## What is in this repository

This repository contains the Canis Docker/browser submission in `track_2b/`.
The original template directories for the other tracks have been removed.

| Path | What it is |
| --- | --- |
| `Makefile` | Delegates `make run`, `make run-model`, and `make test` to `track_2b/`. |
| `track_2b/README.md` | Judge-facing setup, runtime, model, and submission notes. |
| `track_2b/ARCHITECTURE.md` | Detailed Docker/web/backend/source/readout architecture. |
| `track_2b/technical_report.md` | Markdown version of the technical report. |
| `track_2b/CanisApertusLab_Report.pdf` | PDF technical report for submission. |
| `track_2b/src/` | FastAPI backend, disposition code, source flow, and built browser UI. |
| `track_2b/docs/` | Report figures and disposition header assets. |
| `track_2b/data/` | Empty placeholder; no dataset is bundled. |

## Quick start

From the repository root:

```bash
make run
```

This builds the lightweight Docker image, starts the local web app, prints the
URL, and opens the browser. Use `OPEN=0 make run` for headless review or
`PORT=8081 make run` if port 8080 is already occupied.

For the real Apertus path:

```bash
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
make run-model
```

`make run-model` loads `swiss-ai/Apertus-v1.5-8B` through Swiss AI's
Transformers branch and mounts the host Hugging Face cache. Model weights are
not committed to this repository.

## Product summary

Canis has two product paths:

- The iOS app is the product reference implementation: local MLX inference,
  private document packs, and a polished Canis interface.
- This Track 2B Docker repo is the reproducible judge/on-premise version:
  browser UI, FastAPI backend, source upload, Docker startup, and optional
  Apertus 1.5 8B runtime.

The Docker path is slower than the iOS MLX path, especially on CPU/offload-heavy
hardware. The UI includes progress and intermezzo content so users understand
that local inference is still running.

## Why it matters

Canis demonstrates the commercial value of Apertus and open weights:

- better user understanding of model answers,
- local/private inference without overseas API traffic,
- source-grounded answers from user documents,
- explainability telemetry for enterprise workflows,
- and a concrete interface for public education around Swiss open models.

See [track_2b/ARCHITECTURE.md](track_2b/ARCHITECTURE.md) for system details and
[track_2b/technical_report.md](track_2b/technical_report.md) for the full
submission narrative.

## License

All Hack Apertus projects are open-sourced. Please check the HackApertus terms
for specific licensing details:
https://hackapertus.ch/terms-and-conditions
