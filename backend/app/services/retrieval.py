from __future__ import annotations

from app.core.config import settings
from app.models.search import SearchHit
from app.services.embedding import embedding_service
from app.services.store import vector_store


def _where_filter(
    university_code: str | None,
    admission_year: int | None,
    method_id: str | None,
    program_code: str | None,
    program_type: str | None,
) -> dict:
    clauses = []
    if university_code:
        clauses.append({"university_code": university_code.upper()})
    if admission_year is not None:
        clauses.append({"admission_year": str(admission_year)})
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


class RetrievalService:
    def search(
        self,
        query: str,
        top_k: int | None = None,
        university_code: str | None = None,
        admission_year: int | None = None,
        method_id: str | None = None,
        program_code: str | None = None,
        program_type: str | None = None,
    ) -> list[SearchHit]:
        k = top_k or settings.top_k
        collection = vector_store.get_collection()
        where = _where_filter(
            university_code, admission_year, method_id, program_code, program_type
        )
        query_vector = embedding_service.embed_texts([query])[0]
        result = collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where if where else None,
        )

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        hits: list[SearchHit] = []
        for idx, chunk_id in enumerate(ids):
            distance = distances[idx] if idx < len(distances) else 1.0
            score = max(0.0, 1.0 - float(distance))
            hits.append(
                SearchHit(
                    chunk_id=chunk_id,
                    score=score,
                    text=docs[idx] if idx < len(docs) else "",
                    metadata=metas[idx] if idx < len(metas) and metas[idx] else {},
                )
            )

        return hits


retrieval_service = RetrievalService()
