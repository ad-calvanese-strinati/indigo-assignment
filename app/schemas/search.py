from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(description="Natural-language search query.")
    limit: int | None = Field(default=None, description="Optional max number of results.")
    tags: list[str] | None = Field(
        default=None,
        description="Optional tag filters applied before semantic ranking.",
    )
    document_identifiers: list[str] | None = Field(
        default=None,
        description="Optional document IDs or exact filenames to restrict the search scope.",
    )


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    tags: list[str]
    score: float = Field(description="Hybrid relevance score after reciprocal rank fusion.")
    matched_by: list[str] = Field(
        description="Retrieval signals that contributed to the final rank, such as dense and lexical.",
    )
    dense_score: float | None = Field(default=None, description="Raw dense retrieval score, when available.")
    lexical_score: float | None = Field(
        default=None,
        description="Raw lexical full-text ranking score, when available.",
    )
    page_number: int | None = None
    section_heading: str | None = None
    excerpt: str = Field(description="Short preview of the matching chunk for quick inspection.")
    content: str


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: list[SearchResult]
