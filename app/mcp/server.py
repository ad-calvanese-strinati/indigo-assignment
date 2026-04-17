from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.repositories.documents import DocumentRepository
from app.services.search import SearchService

settings = get_settings()
mcp = FastMCP(
    "Indigo Knowledge Base",
    instructions=(
        "Use these tools to inspect the enterprise knowledge base before answering user questions. "
        "Prefer targeted searches by tag or document when the user already hints at a business domain, "
        "policy area, or specific source. Use broader semantic search when the request is exploratory."
    ),
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


@mcp.tool(
    description=(
        "List every document currently indexed in the knowledge base. Use this before filtering by "
        "specific documents, or when the user asks what sources are available."
    )
)
async def list_documents() -> dict[str, list[dict[str, object]]]:
    async with session_scope() as session:
        documents = await DocumentRepository(session).list_all()
        return {
            "documents": [
                {
                    "id": document.id,
                    "filename": document.filename,
                    "tags": document.tags,
                    "upload_date": document.upload_date.isoformat(),
                    "chunk_count": document.chunk_count,
                }
                for document in documents
            ]
        }


@mcp.tool(
    description=(
        "Return all unique tags currently used in the knowledge base. Use this to discover available "
        "business domains such as compliance, onboarding, HR, or product."
    )
)
async def list_tags() -> dict[str, list[str]]:
    async with session_scope() as session:
        tags = await DocumentRepository(session).list_tags()
        return {"tags": tags}


@mcp.tool(
    description=(
        "Run semantic search across the full knowledge base. Use this when the user asks an open-ended "
        "question and no document or tag filter is known yet."
    )
)
async def search(
    query: str,
    limit: int = settings.default_search_limit,
    min_score: float = 0.0,
) -> dict[str, object]:
    async with session_scope() as session:
        response = await SearchService(session).search(query=query, limit=limit)
        filtered = [result.model_dump() for result in response.results if result.score >= min_score]
        return {"query": query, "total_results": len(filtered), "results": filtered}


@mcp.tool(
    description=(
        "Run semantic search restricted to documents matching one or more tags. Use this when the request "
        "already points to a domain like compliance, onboarding, product, HR, or another known tag."
    )
)
async def search_by_tag(
    query: str,
    tags: list[str],
    limit: int = settings.default_search_limit,
    min_score: float = 0.0,
) -> dict[str, object]:
    async with session_scope() as session:
        response = await SearchService(session).search(query=query, limit=limit, tags=tags)
        filtered = [result.model_dump() for result in response.results if result.score >= min_score]
        return {
            "query": query,
            "applied_tags": tags,
            "total_results": len(filtered),
            "results": filtered,
        }


@mcp.tool(
    description=(
        "Run semantic search restricted to one or more known documents. Accepts document IDs or exact "
        "filenames. Use this when the user mentions a specific source document or asks to compare a small "
        "set of known files."
    )
)
async def search_by_document(
    query: str,
    document_identifiers: list[str],
    limit: int = settings.default_search_limit,
    min_score: float = 0.0,
) -> dict[str, object]:
    async with session_scope() as session:
        response = await SearchService(session).search(
            query=query,
            limit=limit,
            document_identifiers=document_identifiers,
        )
        filtered = [result.model_dump() for result in response.results if result.score >= min_score]
        return {
            "query": query,
            "applied_document_identifiers": document_identifiers,
            "total_results": len(filtered),
            "results": filtered,
        }
