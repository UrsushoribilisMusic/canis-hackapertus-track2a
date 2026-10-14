# Canis Apertus Lab — Technical Report

**Track:** HackApertus Track 2B — Own Project  
**Team:** Canis Apertus Lab  
**Demo video:** submitted separately via the HackApertus form  
**Repository:** https://github.com/UrsushoribilisMusic/canis-hackapertus-track2b  

## 1. Vision: What Canis Proves

Canis brings the advantages of Apertus to people by making open weights visible in everyday use. The first benefit we expose is model disposition: because Apertus is open, Canis can inspect internal model signals and show whether an answer appears **confident, unsure, curious, concerned, reluctant, warm, or neutral**.

The product thesis is simple: if society and industry are going to rely on local AI, users need more than polished text. They need signals that make the answer inspectable. That signal is possible because the model is open, local, and available for inspection rather than hidden behind a closed API.

**Prototype delivered.** Canis includes a working iOS app using local MLX inference and a Dockerized browser demo for judges. Judges can run the Docker package with `make run`; the UI opens locally, supports chat, and lets users upload PDF, text, or Markdown sources for grounded answers. The real-model path uses `swiss-ai/Apertus-v1.5-8B` through a local Hugging Face cache.

**Judge test drive.** Run `make run`, ask “What are truffles?”, then upload a small PDF/text/Markdown file and ask a question about it. No API key or model download is required for this deterministic review path.

**Why this matters.** Canis demonstrates a path from research to product:

- **Purposeful AI:** demonstrate the benefit of a Swiss open model by exposing information closed APIs do not provide: a local model-state signal alongside each answer.
- **Technical rigour:** a forward-only hidden-state/J-space method evaluated across Apertus-4B, Ministral-3B, and Qwen3-4B with controls.
- **Value and scalability:** local inference reduces per-query cost, cloud traffic, and environmental footprint; the readout supports filtering, escalation, and review workflows.
- **Sovereign deployability:** prompts, documents, model weights, and model inspection can run on-device or on-premise without transatlantic API traffic.
- **Feasibility:** a working iOS app, a Docker prototype, a source-upload flow, and reproducible run commands are included.

## 2. User Experience

The user asks a question. Canis returns an answer plus a compact readout, for example:

> **Confident — 98% certain**  
> “Truffles are a type of mushroom...”

The readout is intentionally not a mascot mood. It is a compact interface for model-state inspection, enabled by having open model weights available rather than relying on an opaque hosted API. When sources are enabled, the user can add private documents, Canis chunks them locally, retrieves relevant passages, and cites the snippets used for the answer.

The iOS app is the product reference implementation. It runs local models through MLX on Apple silicon, which is much faster than the portable Docker path. The Docker version prioritizes reproducibility for judges and on-premise deployment, while the iOS app shows the intended end-user experience.

## 3. Architecture

The Docker submission has three layers:

1. **Browser UI** served from `src/web/`, matching the Canis app interaction model.
2. **FastAPI backend** exposing health, model, chat, source, and disposition endpoints.
3. **Runtime layer** selecting deterministic mock mode or the real Apertus path.

Default mode:

```bash
make run
```

This builds and starts the local Docker app, prints the URL, and opens the browser. It is deterministic and quick enough for review.

Real Apertus mode:

```bash
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
make run-model
```

The package does **not** bundle Apertus weights. This runs `swiss-ai/Apertus-v1.5-8B` through Swiss AI's Transformers branch, mounts the host Hugging Face cache, and attempts the hidden-state readout. If the model is already installed locally, Canis reuses it through the mounted cache. If not, and the user provides an authorized Hugging Face token, Transformers downloads the full gated model into that cache before the first answer.

## 4. Disposition Readout Method

Canis uses a forward-only readout over the model residual stream. At an internal layer, the hidden state is projected into a vocabulary/logit-lens space. We call this **J-space**. Canis then scores that vector against per-disposition directions and returns the strongest disposition plus a certainty-style distribution over alternatives.

The final product dispositions are:

| Disposition | Meaning |
| --- | --- |
| Confident | The model is converging cleanly on an answer. |
| Unsure | The answer is plausible, but the signal is less settled. |
| Curious | The model is exploring context or opening a new line of thought. |
| Concerned | The model appears to detect risk, sensitivity, or a boundary condition. |
| Reluctant | The model is holding back or avoiding an unsafe path. |
| Warm | The model is helpful, supportive, and user-aligned. |

Neutral is shown when no disposition direction dominates.

The important deployment property is that inference remains forward-only. There is no auxiliary neural network, no sparse autoencoder training, and no backpropagation at runtime. The heavier work is a one-time calibration of compact reference directions. On iOS, the readout engine is implemented around MLX tensors: it accepts a tapped hidden state and logits, projects the state with `jlens_projection.json`, cosine-scores it against `seed_vectors.json`, and computes normalized next-token entropy from logits. The current app keeps the same event channel even when the high-level MLX chat API does not expose every hidden-state tap, so the product path is ready for lower-level MLX access without changing the UI.

The evaluation deliberately tested whether the readout was genuinely reading model state rather than surface words in the prompt. The protocol included:

- a **prompt-only** text classifier with no model access,
- **out-of-distribution** prompts with calibration frozen,
- **inter-rater agreement** checks for the labels,
- and a geometric stability check for disposition directions.

One candidate axis, `mischief`, looked plausible in distribution but failed the controls. We removed it from the product readout. This matters: the system is not built around a single attractive accuracy number; it is built around axes that survive validation.

## 5. Evidence and Figures

In the companion disposition study, a discriminant J-space readout reached **89-95% macro recall** with **6-9% false-positive rate** under five-fold cross-validation across three small open models:

These experiments were calibrated on smartphone-class 3B-4B open models, including Apertus-4B, because that is the product constraint for the iOS app. The Docker runtime uses Apertus v1.5 8B to demonstrate the Track 2B deployment path; production deployments should keep a per-model calibration artifact for the exact deployed checkpoint.

| Model | Naive seeds | Discriminant readout |
| --- | ---: | ---: |
| Apertus-4B | 33% recall / 21% FP | **89% recall / 7% FP** |
| Ministral-3B | 27% recall / 18% FP | **95% recall / 9% FP** |
| Qwen3-4B | 55% recall / 21% FP | **92% recall / 6% FP** |

Out of distribution, frozen calibration achieved **79% / 80% / 70% recall** on Apertus / Ministral / Qwen. The prompt-only control reached **45%**, and lexical baselines were **3-15%**. That gap is the central technical result: Canis is reading more than keywords.

Human and model rater agreement also shaped the taxonomy. Four cross-family model judges agreed at **Fleiss' kappa = 0.89**, while three humans agreed at **0.42** on the same 50-item protocol. This supports a careful interpretation: disposition is a model-native regularity, but some labels are more subjective to human observers than others.

Recommended figures for the PDF:

- `docs/report/fig1_controls.pdf` — controls separating model-state signal from prompt-only signal.
- `docs/report/fig2_separability.pdf` — separability of disposition axes.
- `docs/report/fig3_crossaxis.pdf` — cross-axis geometry and entanglement.

## 6. Sources: Local RAG for User Documents

Canis also shows a practical use case for small local models: private document question answering. Users can upload PDFs, Markdown, or text. The backend extracts text, chunks it locally, retrieves passages by lexical overlap, and passes only the relevant snippets into the answer context.

This feature is deliberately simple in the Docker prototype, but it demonstrates the product value:

- user documents remain local to the deployment,
- prompts can be grounded in private sources,
- the UI can show which passages shaped the answer,
- and a small local model becomes useful for everyday private knowledge work.

For a judge, this is the bridge from interpretability research to a business-ready application: a local assistant that can answer from private material while exposing an additional model-state signal.

## 7. Value, Cost, Scalability, and Sovereignty

Canis increases the commercial usability of Apertus by adding an inspectability signal that applications can use for filtering, escalation, review workflows, and confidence-aware interfaces. A customer support tool, internal knowledge assistant, medical-administrative helper, or compliance review workflow could treat a reluctant or concerned answer differently from a confident one.

For enterprises, disposition becomes an additional operational parameter for understanding model behavior. It does not replace evaluations, source citations, or human review; it adds a runtime signal that can be logged with the answer and the supporting snippets. This supports:

- answer governance: require review for reluctant, concerned, or unsure answers,
- support escalation: route sensitive answers before they reach customers,
- model monitoring: aggregate dispositions by topic, team, and model version,
- procurement: compare behavior across local open models and hosted APIs,
- explainability: attach model-state evidence to answers and citations,
- data control: keep prompts, documents, and telemetry on-device or on-premise.

The cost story is also important. The iOS path avoids per-query cloud inference costs. The Docker path can run on-premise, and the real-model mode can use locally mounted Apertus weights. Once model files are present, runtime does not require an overseas inference API.

Target Track 2B deployment architecture: **on-premise**. The same architecture can also be adapted to air-gapped or Swiss sovereign-cloud deployments, because the model and source documents can remain under the organization's control.

## 8. Implementation Architecture and Team

### iOS product app

The iOS app is built in SwiftUI and uses MLX Swift, MLXLMCommon, and MLXLLM for local model inference. `ModelDownloadManager` downloads and stores MLX weights on-device. `CanisMLXEngine` manages model residency, token streaming, memory pressure, and thermal handling. `DispositionReadoutEngine` contains the forward-only hidden-state/logit readout. Local knowledge packs use PDFKit, Vision OCR fallback, chunking, and SQLite.

The app currently supports the Apertus MLX path and a small Mistral-family path for local testing. It does not ship model weights inside the app bundle; models are downloaded on first use and stored locally.

### Docker and web demo

The Docker version is a FastAPI/Python service with a browser UI served from `src/web/`. The default mode is deterministic for review; `make run-model` loads `swiss-ai/Apertus-v1.5-8B` with PyTorch/Transformers and attempts hidden-state scoring. Source upload uses local PDF/text/Markdown extraction and chunk retrieval.

The web UI mirrors the Canis interaction model: dog state, answer readout, source manager, history, settings, and “while Canis thinks” intermezzo content for slower Docker inference.

### Team

- **Miguel Seglias:** UI and interaction design.
- **Raphael Anderegg and Luca Tescarini:** core scaffolding and integration support.
- **Miguel Angel Rodriguez Marquez:** backend, disposition readout, source/RAG path, report, and submission coordination.

## 9. Enterprise Reuse Scenarios

The technology can be reused beyond the consumer app as an explainability layer for organizations running Apertus or related open models:

- **Corporate model explainability:** add disposition telemetry to an internal Apertus deployment so teams can inspect not only what the model answered, but how settled or cautious the model appeared.
- **Governed knowledge assistants:** combine source citations and disposition logs for internal manuals, compliance material, or technical support documents.
- **Support and escalation:** route concerned, reluctant, or low-certainty answers to human review before they reach customers.
- **Model version comparison:** track disposition distributions across prompts when evaluating a new local model, quantization, or fine-tune.
- **Sovereign private assistants:** keep documents, prompts, model weights, and telemetry on-device or on-premise while still giving users an understandable trust signal.

## 10. Implementation Feasibility

The submission is runnable and testable:

```bash
make run
make test
PORT=8081 make run
OPEN=0 make run
```

The real model path is available separately because local Docker CPU/offload generation can be slow:

```bash
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
make run-model
```

On our Mac Mini Docker/OrbStack setup, a real Apertus question can take from about a minute to several minutes depending on offload behavior. The UI therefore includes progress states and educational “while Canis thinks” content. The iOS MLX app is much faster and is the intended consumer product path.

## 11. What a Judge Can Verify Quickly

| Try this | What it demonstrates |
| --- | --- |
| `make run` | Reproducible Docker startup, local browser UI, no hosted inference service for the default path. |
| Ask “What are truffles?” | A normal answer plus a disposition readout, e.g. confident with a high certainty score. |
| Upload a PDF/manual | Local chunking and retrieval; Canis answers from snippets instead of sending the whole document away. |
| Switch sources on/off | Difference between model-only answering and private-document grounding. |
| `make test` | Unit coverage for the resolver, source flow, and API contract. |

## 12. Limitations

- The Docker real-model path is slower than the iOS MLX implementation.
- The current Docker readout falls back to lexical scoring only when hidden states or logits are unavailable from the active local Transformers runtime. This keeps `make run` reviewable, but the technical claim rests on the forward-only hidden-state/J-space method evaluated in the companion study.
- The source retrieval prototype uses lexical overlap rather than embeddings; it is sufficient for the demo but should be upgraded to local BM25/embedding or hybrid retrieval for enterprise scale-up.
- The reported disposition study validates the method on small open models and a controlled prompt matrix; more domains and languages should be tested before high-stakes deployment.

## 13. References

- Miguel A. Rodriguez Marquez. *Reading Disposition from Smartphone-Class Open Models: A Forward-Only J-Space Probe on Apertus-4B, Ministral-3B and Qwen3-4B.* 2026.
- HackApertus Track 2B template and judging criteria.
- Swiss AI. `swiss-ai/Apertus-v1.5-8B`.
