from pathlib import Path

from app.core.config import settings
from app.models.ingest import IngestResponse


class IngestService:
    def run(self, data_dir: str | None = None, rebuild_index: bool = False) -> IngestResponse:
        target = Path(data_dir or settings.data_dir)
        files = list(target.glob("*.json")) if target.exists() else []

        _ = rebuild_index
        return IngestResponse(
            status="ok",
            universities_processed=len(files),
            chunks_created=0,
            message="Ingest stub completed. Implement parser/chunking/indexing here.",
        )


ingest_service = IngestService()
