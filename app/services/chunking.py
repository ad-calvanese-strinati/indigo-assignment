from app.core.config import get_settings
from app.services.parsers import ParsedSection

settings = get_settings()


def chunk_sections(sections: list[ParsedSection]) -> list[ParsedSection]:
    chunks: list[ParsedSection] = []
    max_chars = settings.max_chunk_chars
    overlap = settings.chunk_overlap_chars

    for section in sections:
        normalized = " ".join(section.text.split())
        if not normalized:
            continue

        start = 0
        while start < len(normalized):
            end = min(len(normalized), start + max_chars)
            if end < len(normalized):
                split_at = normalized.rfind(" ", start, end)
                if split_at > start + max_chars // 2:
                    end = split_at

            chunk_text = normalized[start:end].strip()
            if chunk_text:
                chunks.append(
                    ParsedSection(
                        text=chunk_text,
                        page_number=section.page_number,
                        section_heading=section.section_heading,
                    )
                )

            if end >= len(normalized):
                break
            start = max(0, end - overlap)

    return chunks
