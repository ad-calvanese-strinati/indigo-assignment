from dataclasses import dataclass, field

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import logger
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.schemas.search import SearchResponse, SearchResult
from app.services.embeddings import embed_texts

settings = get_settings()


@dataclass(slots=True)
class RankedCandidate:
    chunk: DocumentChunk
    document: Document
    dense_rank: int | None = None
    lexical_rank: int | None = None
    dense_score: float | None = None
    lexical_score: float | None = None
    matched_by: set[str] = field(default_factory=set)

    @property
    def hybrid_score(self) -> float:
        score = 0.0
        if self.dense_rank is not None:
            score += 1 / (settings.hybrid_rrf_k + self.dense_rank)
        if self.lexical_rank is not None:
            score += 1 / (settings.hybrid_rrf_k + self.lexical_rank)
        return score


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
        candidate_limit = max(search_limit, settings.hybrid_candidate_limit)
        normalized_tags = sorted({tag.strip().lower() for tag in tags or [] if tag.strip()}) or None
        normalized_document_identifiers = (
            sorted({identifier.strip() for identifier in document_identifiers or [] if identifier.strip()}) or None
        )

        logger.info(
            "search.executed query=%r limit=%s tags=%s document_identifiers=%s mode=hybrid",
            query,
            search_limit,
            normalized_tags,
            normalized_document_identifiers,
        )

        query_embedding = (await embed_texts([query]))[0]
        dense_rows = await self._dense_candidates(
            query_embedding,
            candidate_limit=candidate_limit,
            tags=normalized_tags,
            document_identifiers=normalized_document_identifiers,
        )
        lexical_rows = await self._lexical_candidates(
            query,
            candidate_limit=candidate_limit,
            tags=normalized_tags,
            document_identifiers=normalized_document_identifiers,
        )

        logger.info(
            "search.candidates query=%r dense_candidates=%s lexical_candidates=%s",
            query,
            len(dense_rows),
            len(lexical_rows),
        )

        fused = _fuse_ranked_candidates(dense_rows, lexical_rows)
        filtered_candidates = [candidate for candidate in fused if _is_candidate_relevant(candidate)]
        top_candidates = filtered_candidates[:search_limit]
        results = [
            SearchResult(
                chunk_id=candidate.chunk.id,
                document_id=candidate.document.id,
                document_name=candidate.document.filename,
                tags=candidate.document.tags,
                score=candidate.hybrid_score,
                matched_by=sorted(candidate.matched_by),
                dense_score=candidate.dense_score,
                lexical_score=candidate.lexical_score,
                page_number=candidate.chunk.page_number,
                section_heading=candidate.chunk.section_heading,
                excerpt=_build_excerpt(candidate.chunk.content),
                content=candidate.chunk.content,
            )
            for candidate in top_candidates
        ]

        logger.info(
            "search.completed query=%r results=%s filtered_candidates=%s tags=%s document_identifiers=%s mode=hybrid",
            query,
            len(results),
            len(filtered_candidates),
            normalized_tags,
            normalized_document_identifiers,
        )
        return SearchResponse(query=query, total_results=len(results), results=results)

    async def _dense_candidates(
        self,
        query_embedding: list[float],
        *,
        candidate_limit: int,
        tags: list[str] | None,
        document_identifiers: list[str] | None,
    ) -> list[tuple[DocumentChunk, Document, float]]:
        similarity = (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label("dense_score")
        stmt: Select[tuple[DocumentChunk, Document, float]] = (
            select(DocumentChunk, Document, similarity)
            .join(Document, Document.id == DocumentChunk.document_id)
            .order_by(similarity.desc())
            .limit(candidate_limit)
        )
        stmt = _apply_filters(stmt, tags=tags, document_identifiers=document_identifiers)
        rows = (await self.session.execute(stmt)).all()
        return [(chunk, document, float(score)) for chunk, document, score in rows]

    async def _lexical_candidates(
        self,
        query: str,
        *,
        candidate_limit: int,
        tags: list[str] | None,
        document_identifiers: list[str] | None,
    ) -> list[tuple[DocumentChunk, Document, float]]:
        tsvector = func.to_tsvector("simple", DocumentChunk.content)
        tsquery = func.websearch_to_tsquery("simple", query)
        rank = func.ts_rank_cd(tsvector, tsquery).label("lexical_score")

        stmt: Select[tuple[DocumentChunk, Document, float]] = (
            select(DocumentChunk, Document, rank)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(tsvector.op("@@")(tsquery))
            .order_by(rank.desc())
            .limit(candidate_limit)
        )
        stmt = _apply_filters(stmt, tags=tags, document_identifiers=document_identifiers)
        rows = (await self.session.execute(stmt)).all()
        return [(chunk, document, float(score)) for chunk, document, score in rows]


def _apply_filters(
    stmt: Select,
    *,
    tags: list[str] | None,
    document_identifiers: list[str] | None,
) -> Select:
    if tags:
        stmt = stmt.where(Document.tags.op("&&")(tags))

    if document_identifiers:
        stmt = stmt.where(
            (Document.id.in_(document_identifiers)) | (Document.filename.in_(document_identifiers))
        )

    return stmt


def _fuse_ranked_candidates(
    dense_rows: list[tuple[DocumentChunk, Document, float]],
    lexical_rows: list[tuple[DocumentChunk, Document, float]],
) -> list[RankedCandidate]:
    by_chunk_id: dict[str, RankedCandidate] = {}

    for index, (chunk, document, dense_score) in enumerate(dense_rows, start=1):
        candidate = by_chunk_id.setdefault(chunk.id, RankedCandidate(chunk=chunk, document=document))
        candidate.dense_rank = index
        candidate.dense_score = dense_score
        candidate.matched_by.add("dense")

    for index, (chunk, document, lexical_score) in enumerate(lexical_rows, start=1):
        candidate = by_chunk_id.setdefault(chunk.id, RankedCandidate(chunk=chunk, document=document))
        candidate.lexical_rank = index
        candidate.lexical_score = lexical_score
        candidate.matched_by.add("lexical")

    return sorted(
        by_chunk_id.values(),
        key=lambda candidate: (
            candidate.hybrid_score,
            candidate.lexical_score or 0.0,
            candidate.dense_score or 0.0,
        ),
        reverse=True,
    )


def _is_candidate_relevant(candidate: RankedCandidate) -> bool:
    if not _is_meaningful_search_result(candidate.chunk.content):
        return False

    has_strong_lexical_match = (
        candidate.lexical_score is not None and candidate.lexical_score >= settings.min_lexical_score
    )
    has_strong_dense_match = (
        candidate.dense_score is not None and candidate.dense_score >= settings.min_dense_score
    )

    if "lexical" in candidate.matched_by and has_strong_lexical_match:
        return True

    if candidate.matched_by == {"dense"}:
        return has_strong_dense_match

    return has_strong_dense_match or has_strong_lexical_match


def _is_meaningful_search_result(content: str) -> bool:
    normalized = " ".join(content.split())
    if len(normalized) < settings.min_chunk_characters:
        return False

    alpha_characters = sum(1 for char in normalized if char.isalpha())
    return alpha_characters >= settings.min_chunk_alpha_characters


def _build_excerpt(content: str, max_length: int = 240) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_length:
        return normalized

    excerpt = normalized[:max_length]
    last_space = excerpt.rfind(" ")
    if last_space > max_length // 2:
        excerpt = excerpt[:last_space]
    return f"{excerpt.strip()}..."
