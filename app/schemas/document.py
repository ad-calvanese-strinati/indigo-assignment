from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    id: str
    filename: str
    checksum: str
    content_type: str
    tags: list[str]
    upload_date: datetime
    chunk_count: int

    model_config = ConfigDict(from_attributes=True)


class DocumentCreateResult(BaseModel):
    document: DocumentRead
    created: bool = Field(description="False when the upload matched an existing checksum.")


class TagListResponse(BaseModel):
    tags: list[str]
