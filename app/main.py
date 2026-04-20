import contextlib

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

# from app.mcp.server import mcp
from app.mcp.router import router as mcp_router

settings = get_settings()


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as connection:
        await connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        await connection.run_sync(Base.metadata.create_all)
        await connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_document_chunks_content_fts "
            "ON document_chunks USING GIN (to_tsvector('simple', content))"
        )
    # async with mcp.session_manager.run():
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.include_router(mcp_router, prefix="/mcp")

# @app.middleware("http")
# async def fix_host_header(request: Request, call_next):
#     # forza host corretto per MCP
#     request.scope["headers"] = [
#         (k, v)
#         if k != b"host"
#         else (b"host", b"localhost")
#         for (k, v) in request.scope["headers"]
#     ]
#     return await call_next(request)

# app.mount("/mcp", mcp.streamable_http_app())


@app.get("/healthz")
async def public_healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.middleware("http")
async def protect_mcp_and_validate_origin(request: Request, call_next):
    if request.url.path.startswith("/mcp") and request.url.path != "/mcp/tools":
        origin = request.headers.get("origin")
        if origin and origin not in settings.app_allowed_origins:
            return JSONResponse(
                status_code=403, content={"detail": "Origin not allowed."}
            )

        auth_header = request.headers.get("authorization")
        api_key = request.headers.get("x-api-key")
        expected = settings.mcp_auth_token
        values = [auth_header, api_key]
        allowed = any(
            value == expected
            or (value and value.startswith("Bearer ") and value[7:].strip() == expected)
            for value in values
        )
        if not allowed:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid authentication token."},
            )

    return await call_next(request)
