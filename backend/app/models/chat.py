from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User input question")
    session_id: str | None = Field(default=None, description="Optional chat session id")
    university_code: str | None = None
    admission_year: int | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str | None = None
    used_chunks: int = 0
    data_sufficient: bool = True
    note: str | None = None
