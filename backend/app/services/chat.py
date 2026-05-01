from app.models.chat import ChatResponse
from app.services.retrieval import retrieval_service


class ChatService:
    def answer(self, query: str, session_id: str | None = None) -> ChatResponse:
        hits = retrieval_service.search(query=query)

        return ChatResponse(
            answer=(
                "Day la skeleton backend. Chua tich hop LLM. "
                "Ban hay ket noi retrieval + prompt + OpenRouter de co cau tra loi thuc te."
            ),
            session_id=session_id,
            used_chunks=len(hits),
            note="fallback-stub",
        )


chat_service = ChatService()
