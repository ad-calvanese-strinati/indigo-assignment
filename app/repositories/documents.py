from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_checksum(self, checksum: str) -> Document | None:
        result = await self.session.execute(select(Document).where(Document.checksum == checksum))
        return result.scalar_one_or_none()

    async def get_by_identifiers(self, identifiers: list[str]) -> list[Document]:
        if not identifiers:
            return []
        result = await self.session.execute(
            select(Document).where((Document.id.in_(identifiers)) | (Document.filename.in_(identifiers)))
        )
        return list(result.scalars().unique())

    async def list_all(self) -> list[Document]:
        result = await self.session.execute(select(Document).order_by(Document.upload_date.desc()))
        return list(result.scalars().unique())

    async def list_tags(self) -> list[str]:
        result = await self.session.execute(select(func.unnest(Document.tags)))
        return sorted({tag for tag in result.scalars().all() if tag})

    async def add(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.flush()
        return document

    async def delete(self, document_id: str) -> bool:
        result = await self.session.execute(delete(Document).where(Document.id == document_id))
        return (result.rowcount or 0) > 0
