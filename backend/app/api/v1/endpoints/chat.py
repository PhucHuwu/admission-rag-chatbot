from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse
from app.services.chat import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return chat_service.answer(query=payload.query, session_id=payload.session_id)
