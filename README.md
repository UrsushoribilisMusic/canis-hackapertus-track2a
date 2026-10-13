# Hack Apertus — project template

Template repository for [Hack Apertus](https://hackapertus.ch/) submissions.
Every project keeps almost the same layout, so organizers and judges find the
same things in the same place.

## Select your track

This repository contains the Canis Hack Apertus submission for `track_2b`.
The original template directories for the other tracks have been removed.

## The structure

| Path | What it is |
| --- | --- |
| `README.md` | The challenge description and submission requirements for your track |
| `technical_report.md` | The deeper write-up: architecture, evaluation, limitations |
| `Makefile` | `make run` must spin up your project |
| `src/` | Your code |
| `data/` | Datasets — max. 100 MB |
| `findings/` | Issue files — `track_1a` only |
| `docs/` | Diagrams, notes, longer write-ups |

The submission source lives in `track_2b/`. A root `Makefile` delegates to the
track directory so `make run` works both from this repository root and from
`track_2b/`.

## Run it

Judges run `make run` from the root of the project, on a clean checkout:

```bash
make run
```

`make run` is expected to run the project using Docker, since that
is how the judges will run it.
- If you used other local open-weight models, include instructions for running the project in your technical report.
- Use the following environment variables:
```
LLM_NAME — name and version of the model
LLM_BASE_URL — endpoint base URL
LLM_API_KEY — your API key
```

## Project

Canis is a browser demo and API backend for making an Apertus answer more
inspectable. It returns the model answer together with a Canis disposition
readout: a concise signal for whether the answer appears confident, unsure,
curious, concerned, reluctant, warm, or neutral.

See [track_2b/README.md](track_2b/README.md) for the Track 2B requirements and
Canis-specific runtime notes.

## License

All Hack Apertus projects are open-sourced. Please check our Terms & Conditions for specific licensing details (6. What you build is open source): https://hackapertus.ch/terms-and-conditions
