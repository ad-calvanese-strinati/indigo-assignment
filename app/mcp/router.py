from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.mcp.metadata import TOOLS, INSTRUCTIONS

from app.mcp.tools import (
    list_documents_tool,
    list_tags_tool,
    search_tool,
    search_by_tag_tool,
    search_by_document_tool,
)

router = APIRouter()


@router.get("/tools")
async def get_tools():
    return {
        "instructions": INSTRUCTIONS,
        "tools": TOOLS,
    }


@router.post("")
async def mcp_endpoint(request: Request):
    payload = await request.json()

    method = payload.get("method")
    params = payload.get("params", {})
    request_id = payload.get("id")

    try:
        if method == "list_documents":
            result = await list_documents_tool()

        elif method == "list_tags":
            result = await list_tags_tool()

        elif method == "search":
            result = await search_tool(
                query=params["query"],
                limit=params.get("limit", 5),
                min_score=params.get("min_score", 0.0),
            )

        elif method == "search_by_tag":
            result = await search_by_tag_tool(
                query=params["query"],
                tags=params["tags"],
                limit=params.get("limit", 5),
                min_score=params.get("min_score", 0.0),
            )

        elif method == "search_by_document":
            result = await search_by_document_tool(
                query=params["query"],
                document_identifiers=params["document_identifiers"],
                limit=params.get("limit", 5),
                min_score=params.get("min_score", 0.0),
            )

        else:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": "Method not found"},
                },
            )

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(e)},
            },
        )
