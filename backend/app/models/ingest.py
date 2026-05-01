from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    data_dir: str | None = Field(default=None, description="Override default data directory")
    rebuild_index: bool = Field(default=False, description="Rebuild vector index from scratch")


class IngestResponse(BaseModel):
    status: str
    universities_processed: int
    chunks_created: int
    collection_size: int
    message: str
