# Canis Track 2B Architecture

Canis Track 2B is the reproducible Docker/browser version of Canis. It is built for judges and institutions that want to run the prototype locally, inspect the code path, and optionally connect it to Apertus 1.5 8B weights.

## Goals

- Show the Canis product loop: question, answer, disposition readout, optional private sources.
- Demonstrate the value of open weights by exposing a model-state signal alongside text.
- Run in Docker from a clean checkout with `make run`.
- Keep prompts, uploaded documents, model files, and retrieval artifacts inside the local deployment.
- Provide a real Apertus path without committing model weights to the repository.

## Runtime Modes

### Default Review Mode

```bash
make run
```

This builds the lightweight Docker image, starts FastAPI, serves the browser UI, prints the local URL, and opens the browser unless `OPEN=0` is set.

Default mode uses deterministic answers plus the Canis lexical fallback readout. It is intended to be reliable for judges who need to verify the user flow quickly.

### Real Apertus Mode

```bash
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
make run-model
```

This builds `Dockerfile.model`, installs Swiss AI's pinned Transformers branch, mounts the host Hugging Face cache, and loads `swiss-ai/Apertus-v1.5-8B`.

The repository does not bundle model weights. If the mounted cache already contains the model, Canis reuses it. If not, Transformers downloads the full gated model into the cache after authentication.

Useful knobs:

```bash
PORT=8081 make run
OPEN=0 make run
HF_CACHE=/path/to/huggingface-cache make run-model
CANIS_MAX_NEW_TOKENS=64 make run-model
CANIS_MODEL_ID=swiss-ai/Apertus-v1.5-8B make run-model
```

## Component Map

| Component | Path | Role |
| --- | --- | --- |
| Browser UI | `src/web/` | Built Canis web app: chat, dog state, source manager, history, settings, and progress/intermezzo panels. |
| API server | `src/backend/app.py` | FastAPI application, static file serving, health/model/chat/source endpoints. |
| Runtime resolver | `src/backend/runtime.py` | Chooses deterministic mode or Apertus Transformers mode; generates answers and disposition data. |
| Source pipeline | `src/backend/knowledge.py` | Accepts PDF/text/Markdown uploads, extracts text, chunks documents, retrieves relevant snippets. |
| Disposition types | `src/backend/canis_disposition/types.py` | Shared readout schema used by API responses. |
| Lexical fallback | `src/backend/canis_disposition/lexical.py` | Lightweight deterministic readout when hidden states are unavailable. |
| Hidden directions | `src/backend/canis_disposition/hidden_directions.py` | Scores hidden states against compact disposition vectors. |
| Forward lens | `src/backend/canis_disposition/forward_lens.py` | Projects hidden states into the J-space/logit-lens representation. |
| Model probe | `src/backend/model_probe.py` | Checks Apertus tensor access in the heavy Docker image. |

## Request Flow

1. The browser sends a prompt and source settings to `POST /api/chat`.
2. The backend retrieves relevant source chunks if sources are enabled.
3. Runtime generates an answer:
   - default mode returns deterministic demo text,
   - real mode calls Apertus 1.5 8B through Transformers.
4. Runtime emits a Canis disposition readout:
   - hidden-state/J-space scoring when tensors are available,
   - lexical fallback if the active runtime cannot expose hidden states/logits.
5. The browser renders the answer, disposition label, certainty, source snippets, and progress/intermezzo text.

## Disposition Readout

The product dispositions are:

| Disposition | Meaning |
| --- | --- |
| Confident | The model is converging cleanly on an answer. |
| Unsure | The answer is plausible, but the signal is less settled. |
| Curious | The model is exploring context or opening a new line of thought. |
| Concerned | The model appears to detect risk, sensitivity, or a boundary condition. |
| Reluctant | The model is holding back or avoiding an unsafe path. |
| Warm | The model is helpful, supportive, and user-aligned. |
| Neutral | No disposition direction dominates. |

The research path is forward-only: a hidden state is projected into J-space and cosine-scored against compact disposition directions. The Docker runtime attempts that path with Apertus hidden states. The lexical fallback exists only as a reliability guard so the demo remains usable when a local Transformers build cannot expose the expected tensor contract; the technical claim rests on the hidden-state/J-space method evaluated in the report.

## Source/RAG Flow

The source feature is deliberately local and small:

1. User uploads PDF, Markdown, or text.
2. `KnowledgeStore` extracts text with `pypdf` for PDFs and direct decoding for text files.
3. Documents are chunked into manageable passages.
4. Retrieval uses lexical overlap against the current question.
5. Only selected snippets are inserted into the answer context.
6. The UI shows which snippets were used.

This is enough to demonstrate a useful local assistant. Production deployments should replace lexical retrieval with local BM25, embeddings, or hybrid retrieval, but the privacy and architecture boundary stays the same.

## Deployment Boundary

Canis targets Track 2B architecture **a) on-premise**:

- Docker runs on the organization's infrastructure.
- Uploaded sources stay inside the local backend process.
- Hugging Face model files are mounted from a local cache.
- No hosted inference API is required once weights are present.

The same pattern can be adapted for air-gapped or Swiss sovereign-cloud deployments by preloading model weights and Python/Docker artifacts.

## Known Runtime Limits

- Real Apertus generation in Docker can be slow on CPU or offload-heavy hardware. In our OrbStack/Mac Mini tests, short answers took from about one minute to several minutes.
- Apertus 1.5 requires Swiss AI's pinned Transformers branch at the time of this submission.
- The Docker readout falls back to lexical scoring if hidden states/logits are unavailable.
- The source flow uses lexical retrieval rather than embeddings.

## Validation

```bash
make test
curl -sS http://127.0.0.1:8080/api/health
curl -sS http://127.0.0.1:8080/api/models
```

The report PDF contains the companion disposition-study evidence and the judge-facing summary.
