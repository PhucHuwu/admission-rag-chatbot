from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    university_code: str | None = None
    admission_year: int | None = None
    method_id: str | None = None
    program_code: str | None = None
    program_type: str | None = None


class SearchHit(BaseModel):
    chunk_id: str
    score: float
    text: str
    metadata: dict


class SearchResponse(BaseModel):
    hits: list[SearchHit]
