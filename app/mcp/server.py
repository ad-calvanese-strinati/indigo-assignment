from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.repositories.documents import DocumentRepository
from app.services.search import SearchService

settings = get_settings()
mcp = FastMCP(
    "Indigo Knowledge Base",
    instructions=(
        "Use these tools to inspect the enterprise knowledge base before answering user questions. "
        "Prefer targeted searches by tag or document when the user already hints at a business domain, "
        "policy area, or specific source. Use broader semantic search when the request is exploratory. "
        "If you are unsure which tags or documents exist, call list_tags or list_documents first before searching."
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
        "List every document currently indexed in the knowledge base, including IDs, filenames, tags, "
        "upload dates, and chunk counts. Use this when the user asks what sources are available, when "
        "you need exact document identifiers, or before calling search_by_document."
    )
)
async def list_documents() -> dict[str, list[dict[str, object]]]:
    logger.info("mcp.list_documents invoked")
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
        "Return all unique tags currently used in the knowledge base. Use this before search_by_tag when "
        "you need to discover which business-domain filters actually exist, such as compliance, onboarding, "
        "HR, product, or other team-specific labels."
    )
)
async def list_tags() -> dict[str, list[str]]:
    logger.info("mcp.list_tags invoked")
    async with session_scope() as session:
        tags = await DocumentRepository(session).list_tags()
        return {"tags": tags}


@mcp.tool(
    description=(
        "Run hybrid search across the full knowledge base using dense retrieval plus lexical retrieval. "
        "Use this when the user's question is open-ended and no reliable document or tag filter is known yet. "
        "Arguments: query is required, limit controls result count, and min_score can suppress weak matches."
    )
)
async def search(
    query: str,
    limit: int = settings.default_search_limit,
    min_score: float = 0.0,
) -> dict[str, object]:
    logger.info("mcp.search invoked query=%r limit=%s min_score=%s", query, limit, min_score)
    async with session_scope() as session:
        response = await SearchService(session).search(query=query, limit=limit)
        filtered = [result.model_dump() for result in response.results if result.score >= min_score]
        return {"query": query, "total_results": len(filtered), "results": filtered}


@mcp.tool(
    description=(
        "Run hybrid search restricted to documents matching one or more known tags. Use this when the "
        "request already points to a business domain like compliance, onboarding, product, HR, or another "
        "known tag returned by list_tags. Prefer this over broad search when the domain is clear."
    )
)
async def search_by_tag(
    query: str,
    tags: list[str],
    limit: int = settings.default_search_limit,
    min_score: float = 0.0,
) -> dict[str, object]:
    logger.info(
        "mcp.search_by_tag invoked query=%r tags=%s limit=%s min_score=%s",
        query,
        tags,
        limit,
        min_score,
    )
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
        "Run hybrid search restricted to one or more known documents. Accepts exact document IDs or exact "
        "filenames, ideally discovered through list_documents. Use this when the user mentions a specific "
        "source document, asks to compare a small set of known files, or wants answers grounded in named sources."
    )
)
async def search_by_document(
    query: str,
    document_identifiers: list[str],
    limit: int = settings.default_search_limit,
    min_score: float = 0.0,
) -> dict[str, object]:
    logger.info(
        "mcp.search_by_document invoked query=%r document_identifiers=%s limit=%s min_score=%s",
        query,
        document_identifiers,
        limit,
        min_score,
    )
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
