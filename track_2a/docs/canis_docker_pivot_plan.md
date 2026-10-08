# Canis HackApertus Docker Pivot Plan

Date: 2026-10-08

## Submission Constraint

HackApertus Track 2A expects the project to run from a clean checkout via:

```bash
make run
```

The template explicitly expects Docker. The Canis iOS plan still matters as the product direction, but the hackathon submission needs a second deployment target:

- Dockerized Apertus 8B inference.
- Server-side disposition/J-space calculation.
- Browser UI for demo and judging.

## Key Technical Decision

Do not use Ollama as the primary runtime for the disposition prototype.

Ollama/llama.cpp is convenient for generation, but Canis needs intermediate hidden states, output logits, model head weights and normalization details. Those are the core inputs for the J-space / Jacobian disposition calculation. The first reproducible backend should therefore use Python with PyTorch + Hugging Face Transformers.

Candidate model:

- `swiss-ai/Apertus-v1.5-8B`
- Related checkpoints visible in the Hugging Face registry: `swiss-ai/Apertus-v1.5-8B-base`, `swiss-ai/Apertus-v1.5-8B-SFT`, `swiss-ai/Apertus-v1.5-8B-DPO`, `swiss-ai/Apertus-v1.5-8B-RLVR`.

## Target Architecture

```text
browser UI
  |
  | HTTP /api/models, /api/chat, /api/disposition
  v
FastAPI backend
  |
  | transformers forward(..., output_hidden_states=True)
  v
Apertus 8B model
  |
  | hidden state + logits + lm_head + final norm
  v
Canis disposition engine
  |
  | streamed text + readout
  v
browser UI dog/avatar + token readout
```

## Reuse From Existing Code

### Strong Reuse

- `bitforge-canis` Angular app:
  - existing Canis dog UI
  - mood/disposition components
  - chat state handling
  - generation event contract
  - mock plugin behavior
- `src/app/types/canis-plugin.interface.ts`:
  - already defines the generation event shape judges need to see.
- `canis-web` static explainer:
  - architecture language and figures
  - useful public-facing description
  - can be copied into `docs/` or served as an explainer tab.

### Medium Reuse

- `canis-backend`:
  - ingestion/backend patterns are useful, but this hackathon backend should stay smaller.
  - avoid pulling the whole ingestion stack unless needed for the demo.

### Low Reuse / Needs Port

- iOS MLX disposition implementation:
  - product target is Swift/MLX, but Docker target should be Python/PyTorch.
  - same algorithm, different tensor/runtime plumbing.

## Backend Milestones

1. Create `track_2a/src/backend/` with FastAPI.
2. Add endpoints:
   - `GET /api/health`
   - `GET /api/models`
   - `POST /api/chat`
   - `POST /api/disposition`
3. Load Apertus 8B with Transformers.
4. First pass:
   - generate answer
   - return logits entropy
   - return lexical fallback disposition
5. Second pass:
   - call model with `output_hidden_states=True`
   - read mid-layer hidden state
   - project through lm head / unembedding
   - compute token weights and entropy
6. Third pass:
   - seed-vector scoring for `confident`, `unsure`, `curious`, `concerned`, `reluctant`, `warm`.

## Frontend Milestones

1. Build existing `bitforge-canis` web app as the demo UI.
2. Add an HTTP-backed Canis plugin implementation:
   - same interface as `CanisPlugin`
   - `ask()` POSTs to backend and emits generation events.
3. Disable native model download UX for hackathon mode:
   - model is already "downloaded" because Docker owns it.
4. Keep mock mode available for no-model local UI demos.
5. Serve built app from backend or Nginx in Docker.

## Docker Milestones

1. `docker-compose.yml` with:
   - `backend`
   - optional `frontend`
2. Volume/cache for Hugging Face model files.
3. Environment:
   - `HF_TOKEN` if the model requires gated access.
   - `CANIS_MODEL_ID=swiss-ai/Apertus-v1.5-8B`
   - `CANIS_DEVICE=auto`
4. `Makefile`:
   - `make run` -> `docker compose up --build`

## Prototype Demo Scope

For the team demo, do not wait for perfect J-space fidelity.

Minimum useful prototype:

- Browser opens Canis web UI.
- Prompt box works.
- Backend returns an Apertus-generated answer or a deterministic mock if model unavailable.
- UI shows a disposition readout with:
  - disposition label
  - certainty
  - six leaning tokens
  - source: `forwardLens` when hidden-state path works, otherwise `lexicalFallback`.

## Risks

- Apertus 8B memory footprint may exceed normal laptop Docker resources unless quantized.
- Quantized inference may obscure exact lm head / norm access depending on serving library.
- Transformers path is easiest to inspect, but slower than Ollama/vLLM.
- The existing Angular app may require private Bitforge packages or Bun/Node versions; if build friction is high, use the static `canis-web` page plus a small demo panel first.

## Recommended Immediate Sequence

1. Copy the template into a new public submission repo.
2. Add minimal Docker/FastAPI skeleton with mock Apertus response.
3. Build the Angular UI once and confirm it can run in browser mode.
4. Add HTTP-backed `CanisPlugin`.
5. Wire Docker backend to the UI using the existing event contract.
6. Add real Apertus 8B loading.
7. Port disposition engine from lexical fallback -> hidden-state entropy -> seed-vector scoring.
8. Fill `technical_report.md` with architecture, model usage, limitations and reproducibility.
