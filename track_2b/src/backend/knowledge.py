"""In-memory source store for the Docker demo."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{2,}")


@dataclass
class Section:
    id: str
    title: str
    text: str


@dataclass
class KnowledgePack:
    id: str
    name: str
    created_at: str
    sections: list[Section] = field(default_factory=list)
    size_bytes: int = 0

    def to_web(self, active_id: str | None) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "documentCount": 1,
            "sectionCount": len(self.sections),
            "sizeBytes": self.size_bytes,
            "createdAt": self.created_at,
            "isActive": self.id == active_id,
            "isBuiltIn": False,
        }


class KnowledgeStore:
    def __init__(self) -> None:
        self._packs: dict[str, KnowledgePack] = {}
        self._active_id: str | None = None

    @property
    def active_id(self) -> str | None:
        return self._active_id

    def list(self) -> list[dict]:
        return [pack.to_web(self._active_id) for pack in self._packs.values()]

    def add(self, name: str, data: bytes) -> KnowledgePack:
        text = extract_text(name, data)
        sections = chunk_text(name, text)
        pack = KnowledgePack(
            id=str(uuid.uuid4()),
            name=name,
            created_at=datetime.now(timezone.utc).isoformat(),
            sections=sections,
            size_bytes=len(data),
        )
        self._packs[pack.id] = pack
        self._active_id = pack.id
        return pack

    def activate(self, pack_id: str | None) -> None:
        if pack_id is not None and pack_id not in self._packs:
            raise KeyError(pack_id)
        self._active_id = pack_id

    def rename(self, pack_id: str, name: str) -> None:
        self._packs[pack_id].name = name

    def delete(self, pack_id: str) -> None:
        del self._packs[pack_id]
        if self._active_id == pack_id:
            self._active_id = None

    def search(self, prompt: str, limit: int = 3) -> list[dict]:
        if not self._active_id:
            return []
        pack = self._packs.get(self._active_id)
        if pack is None:
            return []
        query_terms = terms(prompt)
        if not query_terms:
            return []
        scored: list[tuple[int, Section]] = []
        for section in pack.sections:
            score = len(query_terms.intersection(terms(section.text)))
            if score > 0:
                scored.append((score, section))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "sectionId": section.id,
                "citationIndex": index + 1,
                "title": section.title,
                "snippet": snippet(section.text, query_terms),
            }
            for index, (_score, section) in enumerate(scored[:limit])
        ]


def terms(text: str) -> set[str]:
    return {match.group(0).lower() for match in WORD_RE.finditer(text)}


def extract_text(name: str, data: bytes) -> str:
    if name.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError:
            return "PDF text extraction is unavailable in this Docker image."
        from io import BytesIO

        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(page.strip() for page in pages if page.strip())
        return text or "No extractable text was found in this PDF."
    return data.decode("utf-8", errors="replace")


def chunk_text(name: str, text: str, chunk_size: int = 900) -> list[Section]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        paragraphs = [text.strip() or name]
    sections: list[Section] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                sections.append(section_for(name, len(sections), current))
                current = ""
            for part in split_long_text(paragraph, chunk_size):
                sections.append(section_for(name, len(sections), part))
            continue
        if current and len(current) + len(paragraph) > chunk_size:
            sections.append(section_for(name, len(sections), current))
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        sections.append(section_for(name, len(sections), current))
    return sections[:80]


def split_long_text(text: str, chunk_size: int) -> list[str]:
    chunks: list[str] = []
    remaining = text.strip()
    while len(remaining) > chunk_size:
        cut = remaining.rfind(" ", 0, chunk_size)
        if cut < chunk_size // 2:
            cut = chunk_size
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def section_for(name: str, index: int, text: str) -> Section:
    first_line = text.splitlines()[0].strip()
    title = first_line[:80] if first_line else name
    return Section(id=f"{name}-{index + 1}", title=title, text=text)


def snippet(text: str, query_terms: set[str], width: int = 260) -> str:
    lower = text.lower()
    first_hit = min((lower.find(term) for term in query_terms if term in lower), default=0)
    start = max(0, first_hit - 80)
    clipped = text[start : start + width].replace("\n", " ").strip()
    return clipped + ("..." if start + width < len(text) else "")
