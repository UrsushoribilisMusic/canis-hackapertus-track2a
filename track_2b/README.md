# Track 2 B: Own Project

Canis is a working Apertus prototype for making an AI answer more inspectable.
It pairs a browser chat demo with a Dockerized FastAPI backend that can run in
deterministic mock mode or with `swiss-ai/Apertus-v1.5-8B` through Swiss AI's
Transformers branch.

Bring your own idea and build a working Apertus prototype that tackles a problem you care about — any domain, any use case. The project must be new, started within the hackathon period.

Submissions must use the Apertus model family.
For Track 2 this means that submitted solutions must be built with Apertus. Other open-weights models can be used to support development, e.g. as automatic judges during evaluation. Their role must be clearly described in the submission report.

💬 In case you have questions, join the conversation on [Discord](https://discord.gg/hack-apertus) or send an email to “hello@hackapertus.ch”

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

## Run it

From this directory:

```bash
make run
```

Or from the repository root:

```bash
make run
```

Open:

```text
http://127.0.0.1:8080/
```

Current Canis status:

- `make run` starts a Dockerized FastAPI backend and browser demo.
- The default runtime is a deterministic mock plus the Canis lexical fallback
  disposition readout.
- `make run-model` starts the same browser/API app backed by
  `swiss-ai/Apertus-v1.5-8B` through Swiss AI's Transformers branch. It mounts
  the host Hugging Face cache and sets `CANIS_ENABLE_MODEL=1`.
- `make test` runs the stdlib Python unit tests for the disposition resolver.
- `make probe-model` builds the heavier Transformers image and probes Apertus
  tensors using the host Hugging Face cache mounted into Docker.
- `swiss-ai/Apertus-v1.5-8B` is gated on Hugging Face. Export `HF_TOKEN`
  with an authorized token before probing or running the real model path.
- Apertus 1.5 is not supported by the released Transformers package yet; the
  model probe installs Swiss AI's pinned Transformers branch with text/vision
  support. Audio extras are intentionally omitted from the probe image.
- Set `CANIS_MAX_NEW_TOKENS` to tune latency. The default real-model path uses
  `32` and prompts the model to answer in two short complete sentences because
  local CPU/offload generation is slow.
- The submission target remains Apertus 8B with hidden-state/J-space scoring;
  the current real-model path generates answers with Apertus and still uses the
  lexical fallback for the disposition readout while J-space scoring is wired.
- `src/web/` contains the built Canis Angular browser app. The macOS host build
  has previously failed in native Angular cache dependencies, so this bundle was
  produced in a Linux `node:22.22.3-bookworm` container.

## Target architecture

Canis targets Track 2B architecture **a) On-premise**. The prototype is packaged
as Docker images and can run on an organization's own infrastructure. The
default `make run` path is self-contained after image build. The real-model
path uses locally mounted Hugging Face weights/cache and does not require a
hosted inference API at runtime once the model files are present.

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
