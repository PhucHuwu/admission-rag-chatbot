from __future__ import annotations

from app.models.chat import ChatResponse
from app.services.llm import openrouter_service
from app.services.retrieval import retrieval_service

def _build_fallback_hint(university_code: str | None, admission_year: int | None) -> str:
    school = university_code.upper() if university_code else "trường bạn đang hỏi"
    year_text = str(admission_year) if admission_year else "năm hiện tại"
    return (
        f"Nếu dữ liệu chưa đủ cho {school} ({year_text}), hãy trả lời lịch sự rằng hiện chưa có đủ thông tin "
        "trong bộ dữ liệu hiện tại. Không bịa số liệu."
    )


def _soft_insufficient_answer(query: str, university_code: str | None, admission_year: int | None) -> str:
    hint = _build_fallback_hint(university_code, admission_year)
    return openrouter_service.generate(query=query, context_blocks=["Không có ngữ cảnh phù hợp."], fallback_hint=hint)


def _render_answer_from_hits(
    query: str,
    hits: list,
    university_code: str | None,
    admission_year: int | None,
) -> tuple[str, bool, str | None]:
    if not hits:
        try:
            answer = _soft_insufficient_answer(query, university_code, admission_year)
            return (answer, False, "no-hit")
        except Exception:
            return (
                "Xin lỗi, hiện chưa đủ dữ liệu trong bộ crawl để trả lời chính xác câu hỏi này.",
                False,
                "no-hit-fallback",
            )

    lines: list[str] = []
    for hit in hits[:3]:
        text = " ".join(hit.text.split())
        if text:
            lines.append(text[:700])

    if not lines:
        try:
            answer = _soft_insufficient_answer(query, university_code, admission_year)
            return (answer, False, "empty-hit")
        except Exception:
            return (
                "Xin lỗi, hiện chưa đủ dữ liệu trong bộ crawl để trả lời chính xác câu hỏi này.",
                False,
                "empty-hit-fallback",
            )

    fallback_hint = _build_fallback_hint(university_code, admission_year)
    try:
        answer = openrouter_service.generate(
            query=query,
            context_blocks=lines,
            fallback_hint=fallback_hint,
        )
    except Exception:
        answer = "\n\n".join(lines)

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
        hits = retrieval_service.search(
            query=query,
            university_code=university_code,
            admission_year=admission_year,
        )
        answer, sufficient, note = _render_answer_from_hits(
            query=query,
            hits=hits,
            university_code=university_code,
            admission_year=admission_year,
        )

        return ChatResponse(
            answer=answer,
            session_id=session_id,
            used_chunks=len(hits),
            data_sufficient=sufficient,
            note=note,
        )


chat_service = ChatService()
