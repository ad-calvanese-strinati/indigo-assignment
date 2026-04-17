from app.services.parsers import parse_document


def test_plain_text_parser_extracts_section_headings() -> None:
    content = """
    CAPITOLO 1

    Introduzione alla macroeconomia.

    1.1 Domanda aggregata

    La domanda aggregata dipende da consumi e investimenti.
    """.encode("utf-8")

    sections = parse_document(content, "text/plain", "manuale.txt")

    assert len(sections) == 2
    assert sections[0].section_heading == "CAPITOLO 1"
    assert "Introduzione alla macroeconomia" in sections[0].text
    assert sections[1].section_heading == "1.1 Domanda aggregata"
    assert "La domanda aggregata dipende" in sections[1].text
