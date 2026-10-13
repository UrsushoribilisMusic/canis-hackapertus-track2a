"""Probe Apertus model internals required by the Canis disposition lens."""

from __future__ import annotations

import json
import os
import time
from typing import Any


MODEL_ID = os.getenv("CANIS_MODEL_ID", "swiss-ai/Apertus-v1.5-8B")
PROMPT = os.getenv("CANIS_PROBE_PROMPT", "Explain one reason small models can sound confident while wrong.")


def shape_of(value: Any) -> list[int] | None:
    shape = getattr(value, "shape", None)
    return list(shape) if shape is not None else None


def extract_hidden_states(outputs: Any) -> Any:
    if getattr(outputs, "hidden_states", None) is not None:
        return outputs.hidden_states
    nested = getattr(outputs, "language_model_outputs", None)
    if nested is not None and getattr(nested, "hidden_states", None) is not None:
        return nested.hidden_states
    nested = getattr(outputs, "text_model_output", None)
    if nested is not None and getattr(nested, "hidden_states", None) is not None:
        return nested.hidden_states
    return None


def extract_logits(outputs: Any) -> Any:
    if getattr(outputs, "logits", None) is not None:
        return outputs.logits
    nested = getattr(outputs, "language_model_outputs", None)
    if nested is not None and getattr(nested, "logits", None) is not None:
        return nested.logits
    nested = getattr(outputs, "text_model_output", None)
    if nested is not None and getattr(nested, "logits", None) is not None:
        return nested.logits
    return None


def main() -> None:
    started = time.perf_counter()

    import torch
    from transformers import AutoModelForMultimodalLM, AutoProcessor

    dtype_name = os.getenv("CANIS_TORCH_DTYPE", "bfloat16")
    dtype = torch.bfloat16 if dtype_name == "bfloat16" else torch.float16

    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForMultimodalLM.from_pretrained(
        MODEL_ID,
        dtype=dtype,
        device_map=os.getenv("CANIS_DEVICE_MAP", "auto"),
    ).eval()
    load_seconds = time.perf_counter() - started

    messages = [
        {"role": "system", "content": "You are a concise and helpful assistant."},
        {"role": "user", "content": PROMPT},
    ]
    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    )
    device = next(model.parameters()).device
    inputs = {key: value.to(device) for key, value in inputs.items()}

    forward_started = time.perf_counter()
    with torch.no_grad():
        outputs = model(
            **inputs,
            output_hidden_states=True,
            use_cache=False,
        )
    logits = extract_logits(outputs)
    hidden_states = extract_hidden_states(outputs)
    forward_seconds = time.perf_counter() - forward_started

    output_embeddings = model.get_output_embeddings()
    payload = {
        "model_id": MODEL_ID,
        "dtype": str(dtype).replace("torch.", ""),
        "device": str(device),
        "load_seconds": round(load_seconds, 3),
        "forward_seconds": round(forward_seconds, 3),
        "logits_shape": shape_of(logits),
        "hidden_state_count": len(hidden_states or []),
        "last_hidden_shape": shape_of(hidden_states[-1]) if hidden_states else None,
        "output_embeddings_shape": shape_of(output_embeddings.weight) if output_embeddings is not None else None,
        "model_class": model.__class__.__name__,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
