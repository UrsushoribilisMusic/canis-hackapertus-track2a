"""FastAPI entry point for the Canis HackApertus Docker target."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.canis_disposition.lexical import lexical_readout
from backend.runtime import build_runtime


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

app = FastAPI(title="Canis Apertus Docker Prototype", version="0.2.0")
runtime = build_runtime()


class ChatRequest(BaseModel):
    prompt: str
    modelId: str | None = None


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "model": runtime.model_id,
        "runtime": runtime.name,
        "model_loaded": runtime.model_loaded,
    }


@app.get("/api/models")
def models() -> dict:
    return {
        "models": [
            {
                "id": runtime.model_id,
                "name": runtime.display_name,
                "status": "loaded" if runtime.model_loaded else "planned",
                "runtime": runtime.name,
            }
        ]
    }


@app.post("/api/disposition")
def disposition(req: ChatRequest) -> dict:
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    return {"readout": lexical_readout(prompt).to_web()}


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    answer, readout = runtime.answer(prompt)
    return {"answer": answer, "readout": readout.to_web()}


if WEB.exists():
    app.mount("/assets", StaticFiles(directory=WEB), name="assets")


@app.get("/")
@app.get("/index.html")
def index() -> FileResponse:
    return FileResponse(WEB / "index.html")

