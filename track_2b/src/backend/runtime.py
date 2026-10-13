"""Runtime selection for mock and Apertus inference."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from backend.canis_disposition.hidden_directions import hidden_direction_readout
from backend.canis_disposition.lexical import lexical_readout
from backend.canis_disposition.types import DispositionReadout


DEFAULT_MODEL_ID = "swiss-ai/Apertus-v1.5-8B"


def mock_answer_for(prompt: str, sources: list[dict] | None = None) -> str:
    """Small deterministic answer set for the lightweight Docker path."""
    if sources:
        source = sources[0]
        return (
            f"From {source['title']}: {source['snippet']} "
            "Canis is using the matching chunk rather than sending the whole document."
        )
    lower = prompt.lower()
    if any(term in lower for term in ["rain", "raining", "weather"]):
        return (
            "Rain happens when moist air rises, cools, and condenses into cloud droplets. "
            "When those droplets grow heavy enough, gravity pulls them down as rain."
        )
    if any(term in lower for term in ["canis", "disposition", "readout"]):
        return (
            "Canis adds an inspectability layer to an AI answer. It shows whether the model "
            "looks confident, unsure, curious, concerned, reluctant, or warm while producing "
            "the response."
        )
    if any(term in lower for term in ["apertus", "model", "8b", "swiss ai"]):
        return (
            "This submission targets Swiss AI's Apertus v1.5 8B model. The default Docker "
            "runtime is lightweight for judging, and the real model path is available with "
            "make run-model once the gated weights are present in the Hugging Face cache."
        )
    if any(term in lower for term in ["docker", "run-model", "hugging face", "hf_token"]):
        return (
            "Use make run for the fast reproducible demo. Use make run-model with HF_TOKEN "
            "and a mounted ~/.cache/huggingface directory when you want Docker to load the "
            "real Apertus weights."
        )
    return (
        "Here is a concise answer based on the local Docker demo path. Canis returns the "
        "answer together with a disposition readout so the response can be inspected, not "
        "only accepted at face value."
    )


def sources_for(prompt: str) -> list[dict]:
    lower = prompt.lower()
    sources: list[dict] = []
    if any(term in lower for term in ["canis", "disposition", "readout", "certainty", "source"]):
        sources.append(
            {
                "sectionId": "canis-disposition-readout",
                "citationIndex": 1,
                "title": "Canis disposition readout",
                "snippet": "Canis combines answer text, model uncertainty signals, and disposition scoring to expose how the model is leaning.",
            }
        )
    if any(term in lower for term in ["apertus", "model", "8b", "swiss ai"]):
        sources.append(
            {
                "sectionId": "apertus-runtime",
                "citationIndex": len(sources) + 1,
                "title": "Swiss AI Apertus v1.5 8B",
                "snippet": "The Docker prototype can run swiss-ai/Apertus-v1.5-8B through Swiss AI's Transformers branch.",
            }
        )
    if any(term in lower for term in ["docker", "runtime", "local", "on-premise", "backend"]):
        sources.append(
            {
                "sectionId": "docker-track-2b-runtime",
                "citationIndex": len(sources) + 1,
                "title": "Track 2B Docker runtime",
                "snippet": "The submission is packaged for on-premise Docker execution with a FastAPI backend and browser UI.",
            }
        )
    return sources[:3]


@dataclass
class Runtime:
    name: str
    model_id: str
    display_name: str
    model_loaded: bool = False

    def answer(
        self, prompt: str, sources: list[dict] | None = None
    ) -> tuple[str, DispositionReadout, list[dict]]:
        raise NotImplementedError


class MockRuntime(Runtime):
    def __init__(self, model_id: str = DEFAULT_MODEL_ID) -> None:
        super().__init__(
            name="mock",
            model_id=model_id,
            display_name="Apertus v1.5 8B",
            model_loaded=False,
        )

    def answer(
        self, prompt: str, sources: list[dict] | None = None
    ) -> tuple[str, DispositionReadout, list[dict]]:
        answer = mock_answer_for(prompt, sources)
        readout = lexical_readout(answer)
        return answer, readout, sources or sources_for(prompt)


class TransformersRuntime(Runtime):
    """Apertus 1.5 runtime backed by Swiss AI's Transformers branch.

    This class is intentionally lazy and isolated. The default Docker demo remains
    runnable without the heavy model stack; use `make run-model` or set
    `CANIS_ENABLE_MODEL=1` when the image has `torch`, Swiss AI's Transformers branch,
    and access to the gated Apertus cache.
    """

    def __init__(self, model_id: str = DEFAULT_MODEL_ID) -> None:
        super().__init__(
            name="transformers",
            model_id=model_id,
            display_name="Apertus v1.5 8B",
            model_loaded=False,
        )
        self._tokenizer = None
        self._processor = None
        self._model = None

    def _load(self) -> None:
        if self.model_loaded:
            return

        try:
            import torch
            from transformers import AutoModelForMultimodalLM, AutoProcessor
        except ImportError as exc:
            raise RuntimeError(
                "CANIS_ENABLE_MODEL=1 requires torch and Swiss AI's transformers branch"
            ) from exc

        started = time.perf_counter()
        dtype_name = os.getenv("CANIS_TORCH_DTYPE", "bfloat16")
        dtype = torch.bfloat16 if dtype_name == "bfloat16" else torch.float16
        print(
            f"Loading {self.model_id} with dtype={dtype_name} device_map={os.getenv('CANIS_DEVICE_MAP', 'auto')}",
            flush=True,
        )
        self._processor = AutoProcessor.from_pretrained(self.model_id)
        self._model = AutoModelForMultimodalLM.from_pretrained(
            self.model_id,
            dtype=dtype,
            device_map=os.getenv("CANIS_DEVICE_MAP", "auto"),
        ).eval()
        self.model_loaded = True
        print(f"Loaded {self.model_id} in {time.perf_counter() - started:.3f}s", flush=True)

    def answer(
        self, prompt: str, sources: list[dict] | None = None
    ) -> tuple[str, DispositionReadout, list[dict]]:
        self._load()
        assert self._processor is not None
        assert self._model is not None

        import torch

        messages = [
            {
                "role": "system",
                "content": os.getenv(
                    "CANIS_SYSTEM_PROMPT",
                    "You are Canis, a concise assistant. Answer in no more than two short, complete sentences.",
                ),
            },
            {
                "role": "user",
                "content": prompt_with_sources(prompt, sources),
            },
        ]
        inputs = self._processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )
        model_device = next(self._model.parameters()).device
        inputs = {key: value.to(model_device) for key, value in inputs.items()}

        tokenizer = getattr(self._processor, "tokenizer", self._processor)

        generation_started = time.perf_counter()
        with torch.no_grad():
            generated = self._model.generate(
                **inputs,
                max_new_tokens=int(os.getenv("CANIS_MAX_NEW_TOKENS", "32")),
                do_sample=False,
                pad_token_id=getattr(tokenizer, "eos_token_id", None),
            )
        print(
            f"Generated {generated.shape[-1] - inputs['input_ids'].shape[-1]} tokens in "
            f"{time.perf_counter() - generation_started:.3f}s",
            flush=True,
        )
        answer = tokenizer.decode(
            generated[0][inputs["input_ids"].shape[-1] :],
            skip_special_tokens=True,
        ).strip()
        readout = self._readout_from_hidden_states(generated, inputs)
        if readout is None:
            readout = lexical_readout(answer or prompt)
        return answer, readout, sources or sources_for(prompt)

    def _readout_from_hidden_states(self, generated, original_inputs) -> DispositionReadout | None:
        try:
            import torch

            assert self._model is not None
            forward_inputs = {
                key: value
                for key, value in original_inputs.items()
                if key not in {"input_ids", "attention_mask"}
            }
            forward_inputs["input_ids"] = generated
            forward_inputs["attention_mask"] = torch.ones_like(generated)

            with torch.no_grad():
                output = self._model(
                    **forward_inputs,
                    output_hidden_states=True,
                    return_dict=True,
                )
            hidden_states = getattr(output, "hidden_states", None)
            logits = getattr(output, "logits", None)
            if not hidden_states or logits is None:
                return None
            hidden = hidden_states[-1][0, -1, :].detach().float().cpu().tolist()
            last_logits = logits[0, -1, :].detach().float().cpu().tolist()
            return hidden_direction_readout(hidden, last_logits)
        except Exception as exc:  # pragma: no cover - depends on model internals.
            print(f"Canis hidden-state readout unavailable, using lexical fallback: {exc}", flush=True)
            return None


def prompt_with_sources(prompt: str, sources: list[dict] | None = None) -> str:
    if not sources:
        return prompt
    context = "\n".join(
        f"[{source['citationIndex']}] {source['title']}: {source['snippet']}"
        for source in sources
    )
    return (
        "Answer using the provided source excerpts. Cite the relevant bracketed source "
        "number when useful.\n\n"
        f"Sources:\n{context}\n\nQuestion: {prompt}"
    )


def build_runtime() -> Runtime:
    model_id = os.getenv("CANIS_MODEL_ID", DEFAULT_MODEL_ID)
    if os.getenv("CANIS_ENABLE_MODEL") == "1":
        return TransformersRuntime(model_id=model_id)
    return MockRuntime(model_id=model_id)
