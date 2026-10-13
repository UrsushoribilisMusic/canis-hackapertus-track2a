"""FastAPI entry point for the Canis HackApertus Docker target."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.canis_disposition.lexical import lexical_readout
from backend.knowledge import KnowledgeStore
from backend.runtime import build_runtime


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

app = FastAPI(title="Canis Apertus Docker Prototype", version="0.2.0")
runtime = build_runtime()
knowledge = KnowledgeStore()


class ChatRequest(BaseModel):
    prompt: str
    modelId: str | None = None


class ActivateKnowledgeRequest(BaseModel):
    packId: str | None = None


class RenameKnowledgeRequest(BaseModel):
    name: str


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
                "status": "loaded"
                if runtime.model_loaded
                else ("setupRequired" if runtime.name == "mock" else "planned"),
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
    if req.modelId and req.modelId != runtime.model_id:
        raise HTTPException(
            status_code=400,
            detail=f"modelId must be {runtime.model_id}",
        )
    knowledge_sources = knowledge.search(prompt)
    answer, readout, runtime_sources = runtime.answer(prompt, knowledge_sources)
    sources = knowledge_sources or runtime_sources
    return {"answer": answer, "readout": readout.to_web(), "sources": sources}


@app.get("/api/knowledge")
def list_knowledge() -> dict:
    return {"packs": knowledge.list()}


@app.post("/api/knowledge")
async def import_knowledge(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="file is empty")
    pack = knowledge.add(file.filename or "source.txt", data)
    return {"pack": pack.to_web(knowledge.active_id)}


@app.post("/api/knowledge/active")
def activate_knowledge(req: ActivateKnowledgeRequest) -> dict:
    try:
        knowledge.activate(req.packId)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="pack not found") from exc
    return {"packs": knowledge.list()}


@app.post("/api/knowledge/{pack_id}/rename")
def rename_knowledge(pack_id: str, req: RenameKnowledgeRequest) -> dict:
    try:
        knowledge.rename(pack_id, req.name.strip())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="pack not found") from exc
    return {"packs": knowledge.list()}


@app.delete("/api/knowledge/{pack_id}")
def delete_knowledge(pack_id: str) -> dict:
    try:
        knowledge.delete(pack_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="pack not found") from exc
    return {"packs": knowledge.list()}


if (WEB / "assets").exists():
    app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets")


@app.get("/")
@app.get("/index.html")
def index() -> FileResponse:
    return FileResponse(WEB / "index.html")


@app.get("/{path:path}")
def static_or_spa(path: str) -> FileResponse:
    candidate = (WEB / path).resolve()
    if candidate.is_file() and WEB.resolve() in candidate.parents:
        return FileResponse(candidate)
    return FileResponse(WEB / "index.html")
