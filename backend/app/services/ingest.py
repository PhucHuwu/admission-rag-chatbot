from pathlib import Path
import json
from typing import Any

from app.core.config import settings
from app.models.ingest import IngestResponse
from app.services.store import vector_store


def _compact_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return " ".join(str(value).split())


def _chunk_university(data: dict[str, Any]) -> dict[str, Any]:
    uni = data.get("university", {})
    return {
        "chunk_type": "university_metadata",
        "text": "\n".join(
            [
                f"Trường: {_compact_text(uni.get('name'))}",
                f"Mã trường: {_compact_text(uni.get('code'))}",
                f"Viết tắt: {_compact_text(uni.get('short_name'))}",
                f"Khu vực: {_compact_text(', '.join(uni.get('location', [])))}",
                f"Nam tuyển sinh: {_compact_text(data.get('admission_year'))}",
                f"Tổng chỉ tiêu: {_compact_text(data.get('total_quota'))}",
                f"Tổng quan: {_compact_text(data.get('admission_overview'))}",
            ]
        ),
        "metadata": {
            "university_code": _compact_text(uni.get("code")).upper(),
            "university_name": _compact_text(uni.get("name")),
            "location": _compact_text(", ".join(uni.get("location", []))),
            "admission_year": str(data.get("admission_year") or ""),
            "method_id": "",
            "program_code": "",
            "program_type": "",
        },
    }


def _chunk_method(data: dict[str, Any], method: dict[str, Any], idx: int) -> dict[str, Any]:
    uni = data.get("university", {})
    programs = method.get("programs") or []
    program_lines = []
    for p in programs:
        groups = p.get("subject_groups") or []
        groups_text = ", ".join(groups) if groups else "không có"
        program_lines.append(
            f"- {p.get('program_name', '')} | code={p.get('program_code', '')} | type={p.get('program_type', '')} | tổ_hợp={groups_text}"
        )

    text = "\n".join(
        [
            f"Trường: {_compact_text(uni.get('name'))} ({_compact_text(uni.get('code'))})",
            f"Năm: {_compact_text(data.get('admission_year'))}",
            f"Phương thức: {_compact_text(method.get('method_name'))}",
            f"Mô tả: {_compact_text(method.get('description'))}",
            f"Đối tượng: {_compact_text(method.get('eligibility'))}",
            f"Quy chế: {_compact_text(method.get('rules'))}",
            "Danh sách ngành:",
            *program_lines,
        ]
    )

    first_program = programs[0] if programs else {}
    return {
        "chunk_type": "admission_method",
        "text": text,
        "metadata": {
            "university_code": _compact_text(uni.get("code")).upper(),
            "university_name": _compact_text(uni.get("name")),
            "location": _compact_text(", ".join(uni.get("location", []))),
            "admission_year": str(data.get("admission_year") or ""),
            "method_id": _compact_text(method.get("method_id")),
            "program_code": _compact_text(first_program.get("program_code")),
            "program_type": _compact_text(first_program.get("program_type")),
            "method_index": str(idx),
            "has_programs": "1" if programs else "0",
        },
    }


def _chunk_raw(data: dict[str, Any], field: str, label: str) -> dict[str, Any] | None:
    text = _compact_text(data.get(field))
    if not text:
        return None
    uni = data.get("university", {})
    return {
        "chunk_type": field,
        "text": (
            f"Trường: {_compact_text(uni.get('name'))} ({_compact_text(uni.get('code'))})\n"
            f"Năm: {_compact_text(data.get('admission_year'))}\n"
            f"{label}: {text}"
        ),
        "metadata": {
            "university_code": _compact_text(uni.get("code")).upper(),
            "university_name": _compact_text(uni.get("name")),
            "location": _compact_text(", ".join(uni.get("location", []))),
            "admission_year": str(data.get("admission_year") or ""),
            "method_id": "",
            "program_code": "",
            "program_type": "",
        },
    }


def _chunk_cutoff_structured(data: dict[str, Any]) -> list[dict[str, Any]]:
    uni = data.get("university", {})
    cutoff = data.get("cutoff_scores") or {}
    methods = cutoff.get("methods") or []
    chunks: list[dict[str, Any]] = []

    for method in methods:
        method_name = _compact_text(method.get("method_name"))
        method_id = _compact_text(method.get("method_id"))
        year = _compact_text(method.get("year") or cutoff.get("year") or data.get("admission_year"))
        entries = method.get("entries") or []
        lines = []
        for entry in entries:
            groups = entry.get("subject_groups") or []
            groups_text = ", ".join(groups) if groups else "không có"
            lines.append(
                f"- {entry.get('program_name', '')} | code={entry.get('program_code', '')} | tổ_hợp={groups_text} | điểm={entry.get('score', '')}"
            )

        if not lines:
            continue

        chunks.append(
            {
                "chunk_type": "cutoff_scores_structured",
                "text": "\n".join(
                    [
                        f"Trường: {_compact_text(uni.get('name'))} ({_compact_text(uni.get('code'))})",
                        f"Năm điểm chuẩn: {year}",
                        f"Phương thức điểm chuẩn: {method_name}",
                        "Danh sách điểm chuẩn:",
                        *lines,
                    ]
                ),
                "metadata": {
                    "university_code": _compact_text(uni.get("code")).upper(),
                    "university_name": _compact_text(uni.get("name")),
                    "location": _compact_text(", ".join(uni.get("location", []))),
                    "admission_year": str(data.get("admission_year") or ""),
                    "method_id": method_id,
                    "program_code": "",
                    "program_type": "",
                    "cutoff_year": year,
                },
            }
        )
    return chunks


class IngestService:
    def run(self, data_dir: str | None = None, rebuild_index: bool = False) -> IngestResponse:
        target = Path(data_dir or settings.data_dir)
        files = list(target.glob("*.json")) if target.exists() else []
        if rebuild_index:
            vector_store.reset()

        collection = vector_store.get_collection()
        ids: list[str] = []
        docs: list[str] = []
        metadatas: list[dict[str, str]] = []

        for file_path in files:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            uni_code = _compact_text(data.get("university", {}).get("code")).upper() or file_path.stem.upper()

            chunks: list[dict[str, Any]] = []
            chunks.append(_chunk_university(data))

            for idx, method in enumerate(data.get("admission_methods") or []):
                chunks.append(_chunk_method(data, method, idx))

            for field, label in (
                ("cutoff_scores_text", "Điểm chuẩn"),
                ("tuition_text", "Học phí"),
                ("timeline_text", "Thời gian và hồ sơ"),
            ):
                chunk = _chunk_raw(data, field, label)
                if chunk:
                    chunks.append(chunk)

            chunks.extend(_chunk_cutoff_structured(data))

            for idx, chunk in enumerate(chunks):
                ids.append(f"{uni_code}:{chunk['chunk_type']}:{idx}")
                docs.append(chunk["text"])
                metadatas.append(chunk["metadata"])

        if ids:
            collection.upsert(ids=ids, documents=docs, metadatas=metadatas)

        collection_size = collection.count()

        return IngestResponse(
            status="ok",
            universities_processed=len(files),
            chunks_created=len(ids),
            collection_size=collection_size,
            message="Ingest completed and chunks persisted to Chroma.",
        )


ingest_service = IngestService()
