"""Probe Apertus model internals required by the Canis disposition lens."""

from __future__ import annotations

import json
import os
import time


MODEL_ID = os.getenv("CANIS_MODEL_ID", "swiss-ai/Apertus-v1.5-8B")
PROMPT = os.getenv("CANIS_PROBE_PROMPT", "Explain one reason small models can sound confident while wrong.")


def main() -> None:
    started = time.perf_counter()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dtype_name = os.getenv("CANIS_TORCH_DTYPE", "bfloat16")
    dtype = torch.bfloat16 if dtype_name == "bfloat16" else torch.float16

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=dtype,
        device_map=os.getenv("CANIS_DEVICE_MAP", "auto"),
    )
    load_seconds = time.perf_counter() - started

    inputs = tokenizer(PROMPT, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {key: value.to(device) for key, value in inputs.items()}

    forward_started = time.perf_counter()
    with torch.no_grad():
        outputs = model(
            **inputs,
            output_hidden_states=True,
            use_cache=False,
        )
    forward_seconds = time.perf_counter() - forward_started

    output_embeddings = model.get_output_embeddings()
    payload = {
        "model_id": MODEL_ID,
        "dtype": str(dtype).replace("torch.", ""),
        "device": str(device),
        "load_seconds": round(load_seconds, 3),
        "forward_seconds": round(forward_seconds, 3),
        "logits_shape": list(outputs.logits.shape),
        "hidden_state_count": len(outputs.hidden_states or []),
        "last_hidden_shape": list(outputs.hidden_states[-1].shape) if outputs.hidden_states else None,
        "output_embeddings_shape": list(output_embeddings.weight.shape) if output_embeddings is not None else None,
        "model_class": model.__class__.__name__,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

