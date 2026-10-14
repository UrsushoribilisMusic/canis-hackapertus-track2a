# Canis Apertus Lab — Track 2B

Canis is a working Apertus prototype for making an AI answer more inspectable.
It pairs a browser chat demo with a Dockerized FastAPI backend that can run in
deterministic mock mode or with `swiss-ai/Apertus-v1.5-8B` through Swiss AI's
Transformers branch.

The demo returns an answer plus a Canis disposition readout: whether the model
appears confident, unsure, curious, concerned, reluctant, warm, or neutral. It
also supports private source upload, so judges can add a PDF, Markdown, or text
file and ask questions grounded in local snippets.

## Why this project exists

Canis demonstrates a product advantage of open weights. A closed API can return
text, but it usually cannot expose internal model-state signals. Apertus can run
locally and can be inspected, so Canis can add an additional trust signal beside
the answer. That signal can help users, enterprises, and reviewers decide when
an answer looks settled, exploratory, cautious, or in need of escalation.

The companion iOS app is the product reference implementation and runs much
faster with MLX on Apple silicon. This repository is the reproducible Docker
submission for judges and on-premise evaluation.

---

## 🔧 Resources & Tools

Check our resources & tools page for detailed information:
https://hackapertus.notion.site/resources-tools

| Models           | URL                                      |
|------------------|------------------------------------------|
| Apertus v1.5 8B  | [huggingface.co/swiss-ai/Apertus-v1.5-8B](https://huggingface.co/swiss-ai/Apertus-v1.5-8B)  |
| Apertus v1.5 70B | [huggingface.co/swiss-ai/Apertus-v1.5-70B](https://huggingface.co/swiss-ai/Apertus-v1.5-70B) |


## Target architecture (mandatory)

Whatever you build in Track 2B must be deployable in one of these three architectures:

- **a) On-premise** — on the organisation's own infrastructure, under its own administration.
- **b) Air-gapped** — with no external network connection at runtime.
- **c) Sovereign Swiss cloud** — on a cloud platform operated in Switzerland, under Swiss jurisdiction, with Swiss data residency.

---

## Data

The `data/` directory must not exceed 100 MB.

Canis does not require a bundled dataset for the current prototype. Runtime
model weights and Hugging Face caches are not committed to this repository.

---

## Quick start

From this directory:

```bash
make run
```

Or from the repository root:

```bash
make run
```

By default, `make run` prints the local URL and opens the browser once the
Docker server is ready:

```text
http://127.0.0.1:8080/
```

For headless environments, disable browser auto-open:

```bash
OPEN=0 make run
```

If port `8080` is already in use, choose another host port:

```bash
PORT=8081 make run
```

Current Canis status:

- `make run` starts a Dockerized FastAPI backend and browser demo.
- The default runtime is a deterministic mock plus the Canis readout contract.
  It exists so judges can verify the whole interface quickly and reliably.
- `make run-model` starts the same browser/API app backed by
  `swiss-ai/Apertus-v1.5-8B` through Swiss AI's Transformers branch. It mounts
  the host Hugging Face cache and sets `CANIS_ENABLE_MODEL=1`. If `make run`
  is already active, stop it with `Ctrl-C` before running `make run-model`.
- `make test` runs the stdlib Python unit tests for the disposition resolver.
- `make probe-model` builds the heavier Transformers image and probes Apertus
  tensors using the host Hugging Face cache mounted into Docker.
- `swiss-ai/Apertus-v1.5-8B` is gated on Hugging Face. Export `HF_TOKEN`
  with an authorized token before probing or running the real model path.
  Hugging Face tokens usually start with `hf_`; examples use
  `hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` so no real token is committed.
- By default, Canis mounts `~/.cache/huggingface` into Docker. If the Apertus
  files are already in another Hugging Face cache, run
  `HF_CACHE=/path/to/huggingface-cache make run-model`. If the mounted cache
  does not contain `swiss-ai/Apertus-v1.5-8B`, Transformers will download the
  full gated model into that cache before the first answer.
- Real-model answers are intentionally visible in the UI while they run. On
  good hardware a question may take about a minute; on CPU or offload-heavy
  Docker runs, our tests have taken several minutes for one question. The
  moving progress bar means the request is still alive.
- Apertus 1.5 is not supported by the released Transformers package yet; the
  model probe installs Swiss AI's pinned Transformers branch with text/vision
  support. Audio extras are intentionally omitted from the probe image.
- Set `CANIS_MAX_NEW_TOKENS` to tune latency. The default real-model path uses
  `32` and prompts the model to answer in two short complete sentences because
  local CPU/offload generation is slow.
- The submission target remains Apertus 8B with hidden-state/J-space scoring.
  The real-model path generates answers with Apertus, then attempts a
  hidden-state forward-lens disposition readout using the compact Canis
  directions artifact. If the active Transformers model does not expose the
  required hidden states/logits, Canis falls back to the lexical readout.
- The browser UI includes the same source upload flow as the iOS app. Uploaded
  PDF, Markdown, and text files are chunked locally inside the Docker backend
  and retrieved as cited snippets for grounded answers.
- `src/web/` contains the built Canis Angular browser app. The macOS host build
  has previously failed in native Angular cache dependencies, so this bundle was
  produced in a Linux `node:22.22.3-bookworm` container.

## What to try

1. Run `make run`.
2. Ask a simple question such as `What are truffles?`.
3. Inspect the answer plus disposition readout.
4. Open Sources, upload a PDF/text/Markdown file, and ask a question about that file.
5. Toggle sources off and ask again to see the difference between model-only and source-grounded answers.

The default path is intentionally deterministic. The real Apertus path is more
interesting technically but much slower on CPU/offload-heavy Docker setups.

## Target architecture

Canis targets Track 2B architecture **a) On-premise**. The prototype is packaged
as Docker images and can run on an organization's own infrastructure. The
default `make run` path is self-contained after image build. The real-model
path uses locally mounted Hugging Face weights/cache and does not require a
hosted inference API at runtime once the model files are present.

## Architecture

The detailed architecture is documented in [ARCHITECTURE.md](ARCHITECTURE.md).
In short:

| Layer | Implementation |
| --- | --- |
| Browser UI | Built Canis web app in `src/web/`, including chat, source manager, history, settings, and progress/intermezzo panels. |
| API backend | FastAPI in `src/backend/app.py`, serving static assets plus health, model, chat, source, and disposition endpoints. |
| Runtime | `src/backend/runtime.py` selects deterministic mode or Apertus Transformers mode. |
| Source/RAG flow | `src/backend/knowledge.py` extracts, chunks, retrieves, and cites local document snippets. |
| Disposition readout | `src/backend/canis_disposition/` contains lexical fallback, hidden-direction scoring, forward-lens projection, entropy helpers, and shared types. |

## Disposition readout

The final product dispositions are:

| Disposition | Meaning |
| --- | --- |
| Confident | The model is converging cleanly on an answer. |
| Unsure | The answer is plausible, but the signal is less settled. |
| Curious | The model is exploring context or opening a new line of thought. |
| Concerned | The model appears to detect risk, sensitivity, or a boundary condition. |
| Reluctant | The model is holding back or avoiding an unsafe path. |
| Warm | The model is helpful, supportive, and user-aligned. |
| Neutral | No disposition direction dominates. |

The research method is forward-only: project the model hidden state into a
J-space/logit-lens representation, score it against compact disposition
directions, and report the strongest direction plus alternatives. The Docker
runtime attempts that path when Apertus hidden states and logits are available.
If the active local Transformers runtime cannot expose those tensors, Canis
falls back to a lexical readout so the demo remains usable. The fallback is a
reliability guard for judge reproducibility; the technical claim is the
forward-only hidden-state/J-space method documented in the report.

## Deliverables

- [technical_report.md](technical_report.md): markdown report.
- [CanisApertusLab_Report.pdf](CanisApertusLab_Report.pdf): PDF report for upload.
- [ARCHITECTURE.md](ARCHITECTURE.md): implementation details.
- `src/`: runnable browser/backend prototype.
- Demo video URL: submitted separately via the HackApertus form.

---

## 📦 Submission Requirements & Deliverables

❗️ Submissions are not handled on Devpost but via this URL only:
http://hackapertus.ch/online-hack/submissions

The submission must: 
1. follow the template repo and include all prerequisite files and definitions
2. follow the specified input/output formats
3. run in a Docker container, launched with `make run` from the root of the project
4. run end-to-end when judges try to run it

### Git repo (URL)
- Create your repo from this template (**Use this template**) and work in the `track_2b/` challenge directory. Delete the other track challenge directories.
- Keep `track_2b/` as it is: don't rename it or move its files.
- Set the repo to PUBLIC (Settings --> Collaborators --> Manage Visibility)
- Submit the URL of YOUR Git repo.

### Technical Report (pdf)
- Update [technical_report.md](technical_report.md) in this repository with all the details for your submission.
- Upload a pdf of your technical report to this directory, named as `TeamName_Report.pdf`.
- Format: pdf, max. 6 pages w/o references
- Submit the pdf of the technical report.

### Demo video (URL)
- Max. 2 min demo video of your prototype

### Dataset (URL) - optional, depending on your project
Submitted datasets must comply with our guidelines for responsibly sourced datasets.

- Create a user account on Hugging Face
- Clone our dataset template on Hugging Face: https://huggingface.co/datasets/HackApertus/online_hack_template
- Complete the dataset card with all required information
- Upload your dataset. It should consist of the following components:
    - evaluation dataset (i.e. individual test cases)
    - model response dataset (i.e. the model response to each test case)
    - metadata file (i.e. additional information about each test case; where relevant, this file must contain instance-level licensing information) 
- Make sure your dataset access control is set to PUBLIC
- Provide the URL of _your_ data set


---

## ⚖️ Judging Criteria

1. Purposeful use of AI
2. Technical rigour
3. Value, cost & scalability
4. Sovereign deployability
5. Implementation feasibility

Judges use a Scale 0–5 per dimension.

---

## Support

**Licensing requirements**
Please check our Terms & Conditions (6. What you build is open source):
https://hackapertus.ch/terms-and-conditions

## FAQ
💡 https://hackapertus.ch/faq

## Contact
💬 In case you have questions, join the conversation on Discord or send an email to “hello@hackapertus.ch”
