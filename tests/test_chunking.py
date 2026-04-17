from app.services.chunking import chunk_sections
from app.services.parsers import ParsedSection


def test_chunking_preserves_page_number() -> None:
    sections = [ParsedSection(text="word " * 600, page_number=3)]
    chunks = chunk_sections(sections)

    assert len(chunks) > 1
    assert all(chunk.page_number == 3 for chunk in chunks)
