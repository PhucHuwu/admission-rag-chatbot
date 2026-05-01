from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import settings


class VectorStore:
    def __init__(self) -> None:
        Path(settings.chroma_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.chroma_dir)
        self.collection = self.client.get_or_create_collection(name=settings.chroma_collection)

    def reset(self) -> None:
        self.client.delete_collection(settings.chroma_collection)
        self.collection = self.client.get_or_create_collection(name=settings.chroma_collection)

    def get_collection(self) -> Collection:
        return self.collection


vector_store = VectorStore()
