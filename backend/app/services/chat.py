from __future__ import annotations

import re

from app.models.chat import ChatResponse
from app.services.llm import openrouter_service
from app.services.retrieval import retrieval_service


def _build_fallback_hint(university_code: str | None) -> str:
    school = university_code.upper() if university_code else "trường bạn đang hỏi"
    return (
        f"Nếu dữ liệu chưa đủ cho {school}, hãy trả lời lịch sự rằng hiện chưa có đủ thông tin "
        "trong bộ dữ liệu hiện tại. Dữ liệu chỉ áp dụng cho mùa tuyển sinh 2025. Không bịa số liệu."
    )


def _extract_years(query: str) -> list[int]:
    years: list[int] = []
    for m in re.findall(r"\b(19\d{2}|20\d{2})\b", query):
        y = int(m)
        if y not in years:
            years.append(y)
    return years


def _year_scope_notice(query: str) -> str | None:
    years = _extract_years(query)
    if not years:
        return None
    if all(y == 2025 for y in years):
        return None
    return "Lưu ý: bộ dữ liệu hiện tại chỉ bao phủ thông tin tuyển sinh năm 2025."


def _soft_insufficient_answer(query: str, university_code: str | None) -> str:
    hint = _build_fallback_hint(university_code)
    return openrouter_service.generate(
        query=query, context_blocks=["Không có ngữ cảnh phù hợp."], fallback_hint=hint
    )


def _render_answer_from_hits(
    query: str,
    hits: list,
    university_code: str | None,
) -> tuple[str, bool, str | None]:
    year_notice = _year_scope_notice(query)

    if not hits:
        try:
            answer = _soft_insufficient_answer(query, university_code)
            if year_notice:
                answer = f"{year_notice}\n\n{answer}"
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
            answer = _soft_insufficient_answer(query, university_code)
            if year_notice:
                answer = f"{year_notice}\n\n{answer}"
            return (answer, False, "empty-hit")
        except Exception:
            return (
                "Xin lỗi, hiện chưa đủ dữ liệu trong bộ crawl để trả lời chính xác câu hỏi này.",
                False,
                "empty-hit-fallback",
            )

    fallback_hint = _build_fallback_hint(university_code)
    try:
        answer = openrouter_service.generate(
            query=query,
            context_blocks=lines,
            fallback_hint=fallback_hint,
        )
    except Exception:
        answer = "\n\n".join(lines)

    if year_notice:
        answer = f"{year_notice}\n\n{answer}"

    if "không đủ dữ liệu" in answer.lower():
        return (answer, False, "insufficient-context")
    return (answer, True, None)


class ChatService:
    def answer(
        self,
        query: str,
        session_id: str | None = None,
        university_code: str | None = None,
    ) -> ChatResponse:
        hits = retrieval_service.search(
            query=query,
            university_code=university_code,
        )
        answer, sufficient, note = _render_answer_from_hits(
            query=query,
            hits=hits,
            university_code=university_code,
        )

        return ChatResponse(
            answer=answer,
            session_id=session_id,
            used_chunks=len(hits),
            data_sufficient=sufficient,
            note=note,
        )


chat_service = ChatService()
