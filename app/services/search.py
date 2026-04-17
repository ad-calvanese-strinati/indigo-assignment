from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.schemas.search import SearchResponse, SearchResult
from app.services.embeddings import embed_texts

settings = get_settings()


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self,
        query: str,
        *,
        limit: int | None = None,
        tags: list[str] | None = None,
        document_identifiers: list[str] | None = None,
    ) -> SearchResponse:
        search_limit = max(1, min(limit or settings.default_search_limit, settings.max_search_limit))
        query_embedding = (await embed_texts([query]))[0]

        similarity = (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label("score")
        stmt: Select[tuple[DocumentChunk, Document, float]] = (
            select(DocumentChunk, Document, similarity)
            .join(Document, Document.id == DocumentChunk.document_id)
            .order_by(similarity.desc())
            .limit(search_limit)
        )

        if tags:
            normalized = sorted({tag.strip().lower() for tag in tags if tag.strip()})
            if normalized:
                stmt = stmt.where(Document.tags.op("&&")(normalized))

        if document_identifiers:
            stmt = stmt.where(
                (Document.id.in_(document_identifiers)) | (Document.filename.in_(document_identifiers))
            )

        rows = (await self.session.execute(stmt)).all()
        results = [
            SearchResult(
                chunk_id=chunk.id,
                document_id=document.id,
                document_name=document.filename,
                tags=document.tags,
                score=max(0.0, min(1.0, float(score))),
                page_number=chunk.page_number,
                section_heading=chunk.section_heading,
                excerpt=_build_excerpt(chunk.content),
                content=chunk.content,
            )
            for chunk, document, score in rows
        ]
        return SearchResponse(query=query, total_results=len(results), results=results)


def _build_excerpt(content: str, max_length: int = 240) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_length:
        return normalized

    excerpt = normalized[:max_length]
    last_space = excerpt.rfind(" ")
    if last_space > max_length // 2:
        excerpt = excerpt[:last_space]
    return f"{excerpt.strip()}..."
