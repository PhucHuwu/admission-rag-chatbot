from app.core.config import settings
from app.models.search import SearchHit


class RetrievalService:
    def search(
        self,
        query: str,
        top_k: int | None = None,
        university_code: str | None = None,
        admission_year: int | None = None,
    ) -> list[SearchHit]:
        _ = (query, university_code, admission_year)
        k = top_k or settings.top_k

        return [
            SearchHit(
                chunk_id="stub-1",
                score=0.0,
                text="Stub retrieval result. Implement Chroma search here.",
                metadata={"top_k": k},
            )
        ]


retrieval_service = RetrievalService()
