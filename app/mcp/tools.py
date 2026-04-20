# app/mcp/tools.py

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.repositories.documents import DocumentRepository
from app.services.search import SearchService

settings = get_settings()


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def list_documents_tool():
    logger.info("mcp.list_documents invoked")
    async with session_scope() as session:
        documents = await DocumentRepository(session).list_all()
        return {
            "documents": [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "tags": d.tags,
                    "upload_date": d.upload_date.isoformat(),
                    "chunk_count": d.chunk_count,
                }
                for d in documents
            ]
        }


async def list_tags_tool():
    logger.info("mcp.list_tags invoked")
    async with session_scope() as session:
        tags = await DocumentRepository(session).list_tags()
        return {"tags": tags}


async def search_tool(query: str, limit: int, min_score: float):
    async with session_scope() as session:
        response = await SearchService(session).search(query=query, limit=limit)
        filtered = [r.model_dump() for r in response.results if r.score >= min_score]
        return {
            "query": query,
            "total_results": len(filtered),
            "results": filtered,
        }


async def search_by_tag_tool(query, tags, limit, min_score):
    async with session_scope() as session:
        response = await SearchService(session).search(
            query=query, limit=limit, tags=tags
        )
        filtered = [r.model_dump() for r in response.results if r.score >= min_score]
        return {
            "query": query,
            "applied_tags": tags,
            "total_results": len(filtered),
            "results": filtered,
        }


async def search_by_document_tool(query, document_identifiers, limit, min_score):
    async with session_scope() as session:
        response = await SearchService(session).search(
            query=query,
            limit=limit,
            document_identifiers=document_identifiers,
        )
        filtered = [r.model_dump() for r in response.results if r.score >= min_score]
        return {
            "query": query,
            "applied_document_identifiers": document_identifiers,
            "total_results": len(filtered),
            "results": filtered,
        }
