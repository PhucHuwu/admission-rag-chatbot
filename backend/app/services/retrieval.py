from __future__ import annotations

from collections.abc import Mapping
from typing import Any
import re

from app.core.config import settings
from app.models.search import SearchHit
from app.services.embedding import embedding_service
from app.services.store import vector_store


def _where_filter(
    university_code: str | None,
    method_id: str | None,
    program_code: str | None,
    program_type: str | None,
) -> dict:
    clauses = []
    if university_code:
        clauses.append({"university_code": university_code.upper()})
    if method_id:
        clauses.append({"method_id": method_id})
    if program_code:
        clauses.append({"program_code": program_code})
    if program_type:
        clauses.append({"program_type": program_type})
    clauses.append({"chunk_type": "qa_pair"})

    if not clauses:
        return {}
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _first_row(value: Any) -> list[Any]:
    if not isinstance(value, list) or not value:
        return []
    first = value[0]
    if isinstance(first, list):
        return first
    return []


def _metadata_to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


class RetrievalService:
    @staticmethod
    def _normalize_query(query: str) -> str:
        q = " ".join(query.split())
        # Dataset only covers 2025, remove explicit year noise.
        q = re.sub(r"\b(19|20)\d{2}\b", "", q)
        q = re.sub(r"\bnăm\s*\b", "", q, flags=re.IGNORECASE)
        q = re.sub(r"\s+", " ", q).strip()
        return q or query.strip()

    @staticmethod
    def _token_overlap(a: str, b: str) -> float:
        ta = {x for x in re.findall(r"[\wÀ-ỹ]+", a.lower()) if len(x) >= 2}
        tb = {x for x in re.findall(r"[\wÀ-ỹ]+", b.lower()) if len(x) >= 2}
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / max(1, len(ta))

    def _query_once(
        self,
        query: str,
        k: int,
        where: dict | None,
    ) -> list[SearchHit]:
        collection = vector_store.get_collection()
        query_vector = embedding_service.embed_texts([query])[0]
        result = collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where,
        )

        ids = _first_row(result.get("ids"))
        docs = _first_row(result.get("documents"))
        metas = _first_row(result.get("metadatas"))
        distances = _first_row(result.get("distances"))

        hits: list[SearchHit] = []
        for idx, chunk_id in enumerate(ids):
            distance = distances[idx] if idx < len(distances) else 1.0
            score = max(0.0, 1.0 - float(distance))
            hits.append(
                SearchHit(
                    chunk_id=chunk_id,
                    score=score,
                    text=docs[idx] if idx < len(docs) else "",
                    metadata=_metadata_to_dict(metas[idx]) if idx < len(metas) else {},
                )
            )
        return hits

    def search(
        self,
        query: str,
        top_k: int | None = None,
        university_code: str | None = None,
        method_id: str | None = None,
        program_code: str | None = None,
        program_type: str | None = None,
    ) -> list[SearchHit]:
        k = top_k or settings.top_k
        where = _where_filter(
            university_code, method_id, program_code, program_type
        )

        normalized = self._normalize_query(query)
        base_hits = self._query_once(query=query, k=max(k, 8), where=where if where else None)
        if normalized != query:
            base_hits.extend(
                self._query_once(
                    query=normalized,
                    k=max(k, 8),
                    where=where if where else None,
                )
            )

        # Merge duplicate chunks (keep best score)
        merged: dict[str, SearchHit] = {}
        for hit in base_hits:
            old = merged.get(hit.chunk_id)
            if old is None or hit.score > old.score:
                merged[hit.chunk_id] = hit

        # Lightweight lexical rerank to align with cleaned QA text
        reranked: list[SearchHit] = []
        for hit in merged.values():
            overlap = self._token_overlap(normalized, hit.text)
            hit.score = min(1.0, hit.score + 0.12 * overlap)
            reranked.append(hit)

        reranked.sort(key=lambda h: h.score, reverse=True)
        return reranked[:k]


retrieval_service = RetrievalService()
