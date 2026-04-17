from dataclasses import dataclass
from io import BytesIO
import re

from pypdf import PdfReader


@dataclass(slots=True)
class ParsedSection:
    text: str
    page_number: int | None = None
    section_heading: str | None = None


def parse_document(content: bytes, content_type: str, filename: str) -> list[ParsedSection]:
    lowered = filename.lower()
    if content_type == "application/pdf" or lowered.endswith(".pdf"):
        return _parse_pdf(content)
    return _parse_text(content)


def _parse_pdf(content: bytes) -> list[ParsedSection]:
    reader = PdfReader(BytesIO(content))
    sections: list[ParsedSection] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if page_text:
            sections.extend(_split_into_structured_sections(page_text, page_number=index))
    return sections


def _parse_text(content: bytes) -> list[ParsedSection]:
    text = content.decode("utf-8", errors="ignore").strip()
    return _split_into_structured_sections(text) if text else []


def _split_into_structured_sections(text: str, page_number: int | None = None) -> list[ParsedSection]:
    lines = [line.strip() for line in text.splitlines()]
    sections: list[ParsedSection] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in lines:
        if not line:
            continue

        if _looks_like_heading(line):
            if current_lines:
                sections.append(
                    ParsedSection(
                        text="\n".join(current_lines).strip(),
                        page_number=page_number,
                        section_heading=current_heading,
                    )
                )
                current_lines = []
            current_heading = _normalize_heading(line)
            continue

        current_lines.append(line)

    if current_lines:
        sections.append(
            ParsedSection(
                text="\n".join(current_lines).strip(),
                page_number=page_number,
                section_heading=current_heading,
            )
        )

    if not sections and text.strip():
        sections.append(
            ParsedSection(
                text=text.strip(),
                page_number=page_number,
                section_heading=None,
            )
        )

    return sections


def _looks_like_heading(line: str) -> bool:
    normalized = " ".join(line.split())
    if len(normalized) < 3 or len(normalized) > 120:
        return False

    if normalized.endswith((".", ",", ";", ":")):
        return False

    words = normalized.split()
    if len(words) > 12:
        return False

    if re.match(r"^\d+(\.\d+)*\s+[A-ZÀ-ÖØ-Ý]", normalized):
        return True

    if re.match(r"^(chapter|capitolo|section|sezione|appendix|appendice)\b", normalized, re.IGNORECASE):
        return True

    letters = [char for char in normalized if char.isalpha()]
    uppercase_ratio = (
        sum(1 for char in letters if char.isupper()) / len(letters)
        if letters
        else 0
    )
    titlecase_ratio = sum(1 for word in words if word[:1].isupper()) / len(words)

    return uppercase_ratio > 0.8 or titlecase_ratio > 0.8


def _normalize_heading(line: str) -> str:
    normalized = " ".join(line.split())
    return normalized[:255]
