from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.mcp.metadata import TOOLS, INSTRUCTIONS
import asyncio
from fastapi.responses import StreamingResponse
import json

from app.mcp.tools import (
    list_documents_tool,
    list_tags_tool,
    search_tool,
    search_by_tag_tool,
    search_by_document_tool,
)

router = APIRouter()


def sse(data: dict):
    return f"data: {json.dumps(data)}\n\n"


def sse_error(request_id, code, message):
    return sse({
        "type": "error",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    })


@router.get("/tools")
async def get_tools():
    return {
        "instructions": INSTRUCTIONS,
        "tools": TOOLS,
    }




@router.post("")
async def mcp_endpoint(request: Request):
    payload = await request.json()

    async def event_stream():
        request_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params", {})

        try:
            # 🔹 evento iniziale
            yield sse({
                "type": "start",
                "id": request_id,
            })

            # 🔹 routing tool
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
                yield sse_error(request_id, -32601, "Method not found")
                return

            # 🔹 stream risultato (chunking opzionale)
            # 🔹 streaming intelligente
            if isinstance(result, dict) and "results" in result:
                for chunk in result["results"]:
                    yield sse({
                        "type": "chunk",
                        "id": request_id,
                        "data": chunk
                    })
                    await asyncio.sleep(0)

                # opzionale: metadati finali
                yield sse({
                    "type": "metadata",
                    "id": request_id,
                    "data": {
                        "total_results": result.get("total_results"),
                        "query": result.get("query"),
                    }
                })
            else:
                # fallback per tool non streamabili
                yield sse({
                    "type": "result",
                    "id": request_id,
                    "data": result
                })

            # 🔹 fine stream
            yield sse({
                "type": "end",
                "id": request_id,
            })

        except Exception as e:
            yield sse_error(request_id, -32000, str(e))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no", 
        },
    )

# @router.post("")
# async def mcp_endpoint(request: Request):
#     payload = await request.json()

#     method = payload.get("method")
#     params = payload.get("params", {})
#     request_id = payload.get("id")

#     try:
#         if method == "list_documents":
#             result = await list_documents_tool()

#         elif method == "list_tags":
#             result = await list_tags_tool()

#         elif method == "search":
#             result = await search_tool(
#                 query=params["query"],
#                 limit=params.get("limit", 5),
#                 min_score=params.get("min_score", 0.0),
#             )

#         elif method == "search_by_tag":
#             if "query" not in params or "tags" not in params:
#                 return JSONResponse(
#                     status_code=400,
#                     content={
#                         "jsonrpc": "2.0",
#                         "id": request_id,
#                         "error": {
#                             "code": -32602,
#                             "message": "Missing required params: query, tags",
#                         },
#                     },
#                 )

#             result = await search_by_tag_tool(
#                 query=params["query"],
#                 tags=params["tags"],
#                 limit=params.get("limit", 5),
#                 min_score=params.get("min_score", 0.0),
#             )

#         elif method == "search_by_document":
#             result = await search_by_document_tool(
#                 query=params["query"],
#                 document_identifiers=params["document_identifiers"],
#                 limit=params.get("limit", 5),
#                 min_score=params.get("min_score", 0.0),
#             )

#         else:
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "jsonrpc": "2.0",
#                     "id": request_id,
#                     "error": {"code": -32601, "message": "Method not found"},
#                 },
#             )

#         return {
#             "jsonrpc": "2.0",
#             "id": request_id,
#             "result": result,
#         }

#     except Exception as e:
#         return JSONResponse(
#             status_code=500,
#             content={
#                 "jsonrpc": "2.0",
#                 "id": request_id,
#                 "error": {"code": -32000, "message": str(e)},
#             },
#         )
