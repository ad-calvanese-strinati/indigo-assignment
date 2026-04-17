import hashlib

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.repositories.documents import DocumentRepository
from app.schemas.document import DocumentRead
from app.schemas.document import DocumentCreateResult
from app.services.chunking import chunk_sections
from app.services.embeddings import embed_texts
from app.services.parsers import parse_document


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = DocumentRepository(session)

    async def upload(
        self, upload_file: UploadFile, tags: list[str]
    ) -> DocumentCreateResult:
        payload = await upload_file.read()
        checksum = hashlib.sha256(payload).hexdigest()
        existing = await self.repository.get_by_checksum(checksum)
        if existing:
            return DocumentCreateResult(
                document=DocumentRead.model_validate(existing),
                created=False,
            )

        sections = parse_document(
            payload, upload_file.content_type or "", upload_file.filename or "document"
        )
        if not sections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded document does not contain extractable text.",
            )

        chunks = chunk_sections(sections)
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded document could not be chunked into searchable text.",
            )
        embeddings = await embed_texts([chunk.text for chunk in chunks])
        raw_text = "\n\n".join(section.text for section in sections)

        document = Document(
            filename=upload_file.filename or "document",
            checksum=checksum,
            content_type=upload_file.content_type or "text/plain",
            tags=sorted({tag.strip().lower() for tag in tags if tag.strip()}),
            raw_text=raw_text,
            chunk_count=len(chunks),
        )
        await self.repository.add(document)

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings, strict=True)
        ):
            self.session.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    page_number=chunk.page_number,
                    section_heading=chunk.section_heading,
                    content=chunk.text,
                    embedding=embedding,
                )
            )

        await self.session.commit()
        await self.session.refresh(document)
        return DocumentCreateResult(
            document=DocumentRead.model_validate(document), created=True
        )

    async def list_documents(self) -> list[Document]:
        return await self.repository.list_all()

    async def list_tags(self) -> list[str]:
        return await self.repository.list_tags()

    async def delete_document(self, document_id: str) -> bool:
        deleted = await self.repository.delete(document_id)
        await self.session.commit()
        return deleted
