from __future__ import annotations

from app.models.chat import ChatResponse
from app.services.llm import openrouter_service
from app.services.retrieval import retrieval_service

CUTOFF_MISSING_CODES = {"DNH", "DQH", "DYH", "TCU", "CIV", "LCDF", "RHM", "RMU"}


def _is_cutoff_query(query: str) -> bool:
    q = query.lower()
    keywords = ["diem chuan", "điểm chuẩn", "diem xet tuyen", "muc diem"]
    return any(k in q for k in keywords)


def _render_answer_from_hits(query: str, hits: list) -> tuple[str, bool, str | None]:
    if not hits:
        return (
            "Không đủ dữ liệu trong bộ crawl hiện tại để tra lời câu hỏi này.",
            False,
            "no-hit",
        )

    lines: list[str] = []
    for hit in hits[:3]:
        text = " ".join(hit.text.split())
        if text:
            lines.append(text[:700])

    if not lines:
        return (
            "Không đủ dữ liệu trong bộ crawl hiện tại để tra lời câu hỏi này.",
            False,
            "empty-hit",
        )

    try:
        answer = openrouter_service.generate(query=query, context_blocks=lines)
    except Exception:
        answer = "\n\n".join(lines)

    if _is_cutoff_query(query) and "không đủ dữ liệu điểm chuẩn" in answer.lower():
        return ("Không đủ dữ liệu điểm chuẩn trong bộ crawl hiện tại.", False, "cutoff-missing")
    if "không đủ dữ liệu" in answer.lower():
        return (answer, False, "insufficient-context")
    return (answer, True, None)


class ChatService:
    def answer(
        self,
        query: str,
        session_id: str | None = None,
        university_code: str | None = None,
        admission_year: int | None = None,
    ) -> ChatResponse:
        if _is_cutoff_query(query) and university_code and university_code.upper() in CUTOFF_MISSING_CODES:
            return ChatResponse(
                answer="Không đủ dữ liệu điểm chuẩn trong bộ crawl hiện tại.",
                session_id=session_id,
                used_chunks=0,
                data_sufficient=False,
                note="cutoff-missing-known-school",
            )

        hits = retrieval_service.search(
            query=query,
            university_code=university_code,
            admission_year=admission_year,
        )
        answer, sufficient, note = _render_answer_from_hits(query=query, hits=hits)

        return ChatResponse(
            answer=answer,
            session_id=session_id,
            used_chunks=len(hits),
            data_sufficient=sufficient,
            note=note,
        )


chat_service = ChatService()
