from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    tags: list[str]
    score: float = Field(description="Similarity score in the range 0..1.")
    page_number: int | None = None
    section_heading: str | None = None
    excerpt: str = Field(description="Short preview of the matching chunk for quick inspection.")
    content: str


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: list[SearchResult]
