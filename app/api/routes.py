from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_api_token
from app.db.session import get_db_session
from app.schemas.document import DocumentCreateResult, DocumentRead, TagListResponse
from app.schemas.search import SearchResponse
from app.services.documents import DocumentService
from app.services.search import SearchService

router = APIRouter(prefix="/api", dependencies=[Depends(require_api_token)])


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/documents", response_model=DocumentCreateResult, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    tags: str = Form(default=""),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentCreateResult:
    service = DocumentService(session)
    parsed_tags = [item.strip() for item in tags.split(",") if item.strip()]
    result = await service.upload(file, parsed_tags)
    return result


@router.get("/documents", response_model=list[DocumentRead])
async def list_documents(session: AsyncSession = Depends(get_db_session)) -> list[DocumentRead]:
    service = DocumentService(session)
    return await service.list_documents()


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, session: AsyncSession = Depends(get_db_session)) -> None:
    service = DocumentService(session)
    deleted = await service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")


@router.get("/tags", response_model=TagListResponse)
async def list_tags(session: AsyncSession = Depends(get_db_session)) -> TagListResponse:
    service = DocumentService(session)
    return TagListResponse(tags=await service.list_tags())


@router.get("/search", response_model=SearchResponse)
async def search_documents(
    query: str,
    limit: int | None = None,
    tags: str | None = None,
    document_ids: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    service = SearchService(session)
    return await service.search(
        query=query,
        limit=limit,
        tags=tags.split(",") if tags else None,
        document_identifiers=document_ids.split(",") if document_ids else None,
    )
