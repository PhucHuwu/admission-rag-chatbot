from fastapi import APIRouter

from app.models.ingest import IngestRequest, IngestResponse
from app.services.ingest import ingest_service

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("", response_model=IngestResponse)
def ingest(payload: IngestRequest) -> IngestResponse:
    return ingest_service.run(data_dir=payload.data_dir, rebuild_index=payload.rebuild_index)
