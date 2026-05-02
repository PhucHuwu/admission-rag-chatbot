from fastapi import APIRouter

from app.models.search import SearchRequest, SearchResponse
from app.services.retrieval import retrieval_service

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(payload: SearchRequest) -> SearchResponse:
    hits = retrieval_service.search(
        query=payload.query,
        top_k=payload.top_k,
        university_code=payload.university_code,
        method_id=payload.method_id,
        program_code=payload.program_code,
        program_type=payload.program_type,
    )
    return SearchResponse(hits=hits)
