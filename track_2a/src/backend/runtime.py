"""Runtime selection for mock and Apertus inference."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from backend.canis_disposition.lexical import lexical_readout
from backend.canis_disposition.types import DispositionReadout


DEFAULT_MODEL_ID = "swiss-ai/Apertus-v1.5-8B"


@dataclass
class Runtime:
    name: str
    model_id: str
    display_name: str
    model_loaded: bool = False

    def answer(self, prompt: str) -> tuple[str, DispositionReadout]:
        raise NotImplementedError


class MockRuntime(Runtime):
    def __init__(self, model_id: str = DEFAULT_MODEL_ID) -> None:
        super().__init__(
            name="mock",
            model_id=model_id,
            display_name="Apertus v1.5 8B",
            model_loaded=False,
        )

    def answer(self, prompt: str) -> tuple[str, DispositionReadout]:
        readout = lexical_readout(prompt)
        answer = (
            "Prototype response: this Docker path will run Apertus 8B and compute the "
            "Canis disposition readout server-side. The current build keeps the API "
            "contract stable while the real hidden-state backend is being wired."
        )
        return answer, readout


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

    def answer(self, prompt: str) -> tuple[str, DispositionReadout]:
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
            {"role": "user", "content": prompt},
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
        return answer, lexical_readout(answer or prompt)


def build_runtime() -> Runtime:
    model_id = os.getenv("CANIS_MODEL_ID", DEFAULT_MODEL_ID)
    if os.getenv("CANIS_ENABLE_MODEL") == "1":
        return TransformersRuntime(model_id=model_id)
    return MockRuntime(model_id=model_id)
