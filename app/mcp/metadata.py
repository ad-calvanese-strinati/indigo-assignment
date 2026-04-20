INSTRUCTIONS = """
Use these tools to inspect the enterprise knowledge base before answering user questions.

Prefer targeted searches by tag or document when the user already hints at a business domain,
policy area, or specific source.

Use broader semantic search when the request is exploratory.

If you are unsure which tags or documents exist, call list_tags or list_documents first before searching.
"""

TOOLS = [
    {
        "name": "list_documents",
        "description": "List all documents with metadata (id, filename, tags, upload date, chunk count).",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_tags",
        "description": "Return all available tags used in the knowledge base.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "search",
        "description": "Run semantic search across all documents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
                "min_score": {"type": "number"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_by_tag",
        "description": "Search restricted to specific tags.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer"},
                "min_score": {"type": "number"},
            },
            "required": ["query", "tags"],
        },
    },
    {
        "name": "search_by_document",
        "description": "Search restricted to specific documents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "document_identifiers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "limit": {"type": "integer"},
                "min_score": {"type": "number"},
            },
            "required": ["query", "document_identifiers"],
        },
    },
]
