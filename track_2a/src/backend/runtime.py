"""Runtime selection for mock and future Apertus inference."""

from __future__ import annotations

import os
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
    """Optional Apertus runtime.

    This class is intentionally lazy and isolated. The Docker prototype should remain
    runnable without the heavy model stack; set `CANIS_ENABLE_MODEL=1` only when the
    image has `torch` and `transformers` installed and the model cache is available.
    """

    def __init__(self, model_id: str = DEFAULT_MODEL_ID) -> None:
        super().__init__(
            name="transformers",
            model_id=model_id,
            display_name="Apertus v1.5 8B",
            model_loaded=False,
        )
        self._tokenizer = None
        self._model = None

    def _load(self) -> None:
        if self.model_loaded:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "CANIS_ENABLE_MODEL=1 requires torch and transformers in the runtime"
            ) from exc

        dtype = torch.bfloat16 if os.getenv("CANIS_TORCH_DTYPE", "bfloat16") == "bfloat16" else torch.float16
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=dtype,
            device_map=os.getenv("CANIS_DEVICE_MAP", "auto"),
        )
        self.model_loaded = True

    def answer(self, prompt: str) -> tuple[str, DispositionReadout]:
        self._load()
        assert self._tokenizer is not None
        assert self._model is not None

        import torch

        inputs = self._tokenizer(prompt, return_tensors="pt")
        model_device = next(self._model.parameters()).device
        inputs = {key: value.to(model_device) for key, value in inputs.items()}

        with torch.no_grad():
            generated = self._model.generate(
                **inputs,
                max_new_tokens=int(os.getenv("CANIS_MAX_NEW_TOKENS", "120")),
                do_sample=False,
            )
        answer = self._tokenizer.decode(
            generated[0][inputs["input_ids"].shape[-1] :],
            skip_special_tokens=True,
        ).strip()
        return answer, lexical_readout(answer or prompt)


def build_runtime() -> Runtime:
    model_id = os.getenv("CANIS_MODEL_ID", DEFAULT_MODEL_ID)
    if os.getenv("CANIS_ENABLE_MODEL") == "1":
        return TransformersRuntime(model_id=model_id)
    return MockRuntime(model_id=model_id)

