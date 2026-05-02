import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.ingest import IngestResponse
from app.services.embedding import embedding_service
from app.services.store import vector_store

logger = logging.getLogger(__name__)


def _compact_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return " ".join(str(value).split())


def _qa_to_document(qa: dict[str, Any], idx: int) -> tuple[str, str, dict[str, Any]]:
    question = _compact_text(qa.get("question"))
    answer = _compact_text(qa.get("answer"))
    university_code = _compact_text(qa.get("university_code")).upper()
    university_name = _compact_text(qa.get("university_name"))
    admission_year = qa.get("admission_year")
    intent = _compact_text(qa.get("intent"))
    data_status = _compact_text(qa.get("data_status"))
    confidence = qa.get("confidence")
    tags = qa.get("tags") or []
    tags_text = ", ".join([_compact_text(t) for t in tags if _compact_text(t)])

    doc_id = f"{university_code or 'UNK'}:qa:{idx}"
    doc_text = f"Hỏi: {question}\nĐáp: {answer}"
    metadata: dict[str, Any] = {
        "university_code": university_code,
        "university_name": university_name,
        "admission_year": str(admission_year or ""),
        "method_id": "",
        "program_code": "",
        "program_type": "",
        "intent": intent,
        "data_status": data_status,
        "tags": tags_text,
        "chunk_type": "qa_pair",
    }
    if isinstance(confidence, (int, float)):
        metadata["confidence"] = float(confidence)
    return doc_id, doc_text, metadata


class IngestService:
    def run(self, data_dir: str | None = None, rebuild_index: bool = False) -> IngestResponse:
        qa_path = Path(data_dir or settings.qa_dataset_path)
        if not qa_path.exists():
            return IngestResponse(
                status="error",
                universities_processed=0,
                chunks_created=0,
                collection_size=0,
                message=f"QA dataset not found at {qa_path}",
            )

        if rebuild_index:
            logger.info("[ingest] rebuild_index=true, resetting collection '%s'", settings.chroma_collection)
            vector_store.reset()

        collection = vector_store.get_collection()
        qa_lines = qa_path.read_text(encoding="utf-8").splitlines()
        total_lines = len(qa_lines)
        logger.info("[ingest] start indexing QA dataset: %s (%d lines)", qa_path, total_lines)

        batch_size = 500
        ids: list[str] = []
        docs: list[str] = []
        metadatas: list[dict[str, Any]] = []
        processed = 0
        schools: set[str] = set()

        def flush_batch() -> None:
            nonlocal ids, docs, metadatas
            if not ids:
                return
            vectors = embedding_service.embed_texts(docs)
            collection.upsert(ids=ids, documents=docs, metadatas=metadatas, embeddings=vectors)
            ids = []
            docs = []
            metadatas = []

        for idx, line in enumerate(qa_lines):
            raw = line.strip()
            if not raw:
                continue
            qa = json.loads(raw)
            doc_id, doc_text, metadata = _qa_to_document(qa, idx)
            ids.append(doc_id)
            docs.append(doc_text)
            metadatas.append(metadata)
            code = str(metadata.get("university_code") or "")
            if code:
                schools.add(code)
            processed += 1

            if len(ids) >= batch_size:
                flush_batch()
                logger.info("[ingest] progress: %d/%d QA items indexed", processed, total_lines)

        flush_batch()
        logger.info("[ingest] completed: %d/%d QA items indexed", processed, total_lines)

        collection_size = collection.count()
        logger.info(
            "[ingest] collection '%s' now has %d vectors across %d schools",
            settings.chroma_collection,
            collection_size,
            len(schools),
        )

        return IngestResponse(
            status="ok",
            universities_processed=len(schools),
            chunks_created=processed,
            collection_size=collection_size,
            message="Ingest completed from QA dataset and persisted to Chroma.",
        )


ingest_service = IngestService()
