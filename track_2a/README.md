# Academia Challenges

Submissions must use the Apertus model family.
For Track 2 this means that submitted solutions must be built with Apertus. Other open-weights models can be used to support development, e.g. as automatic judges during evaluation. Their role must be clearly described in the submission report.

💬 In case you have questions, join the conversation on Discord or send an email to “hello@hackapertus.ch”

## How it works
Pick from 5 academia challenges provided by Swiss academic institutions:

- **FHGR:** AI-Powered Job Interview Coach
- **OpenParlData:** Extracting Parliamentary Affairs from PDFs into One Common Structure
- **OST:** Multilingual Natural Language Inference over Swiss Official Voting Booklets
- **UZH:** Detecting Cross-Lingual Semantic Differences in Swiss Government Websites
- **ZHAW:** See It, Say It, Pick It: Vision-Language Grounding for a Real Robot Arm

The challenges incl. submission and judging criteria are described in our **Getting Started guide**:
https://hackapertus.notion.site/getting-started-guide-onlinehack

## Run it

Keep `track_2a/` as it is: don't rename it or move its files, just delete the
other track directories.

From the root of the project:

```bash
make run
```

Fill in the [Makefile](Makefile) so that it works on a clean checkout. It is
expected to run the project in a Docker container, since that is how the judges
will run it, without relying on anything already installed on your machine.

Requirements: `runtime, hardware, API keys, model weights`

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
  local CPU/offload generation is slow; a smoke test with `8` tokens completed
  and returned `Hello, Canis.`
- The submission target remains Apertus 8B with hidden-state/J-space scoring;
  the current real-model path generates answers with Apertus and still uses the
  lexical fallback for the disposition readout while J-space scoring is wired.
- `src/web/` contains the built Canis Angular browser app. The macOS host build
  currently crashes in native Angular cache dependencies, so this build was
  produced in a Linux `node:22.22.3-bookworm` container.

## Data
The `data/` directory must not exceed 100 MB.


## 📦 Submission Requirements & Deliverables
❗️ Submissions are not handled on Devpost. Submit through our website only:
http://hackapertus.ch/online-hack/submissions

Requirements differ by challenge. See the description of the challenge you are entering for the exact deliverables.


## ⚖️ Judging Criteria
Judging criteria also differ by challenge. See the respective challenge description.


## Support

**Licensing requirements**
Please check our Terms & Conditions (6. What you build is open source):
https://hackapertus.ch/terms-and-conditions

## FAQ
💡 https://hackapertus.ch/faq

## Contact
💬 In case you have questions, join the conversation on Discord or send an email to “hello@hackapertus.ch”
