INSTRUCTIONS = """
You are an assistant connected to an enterprise knowledge base.

Use the available tools to retrieve factual, grounded information before answering user questions.

Tool usage strategy:
- Prefer targeted searches (by tag or by document) when the user clearly refers to a business domain,
  department, or specific source.
- Use broad semantic search when the request is general or exploratory.
- If you are unsure which tags or documents exist, call list_tags or list_documents first.

Important:
- Always base your answers on retrieved results.
- Do not invent information that is not present in the knowledge base.
"""

TOOLS = [
    {
        "name": "list_documents",
        "description": (
            "List all documents currently available in the knowledge base.\n\n"
            "Returns metadata including document IDs, filenames, tags, upload dates, and chunk counts.\n\n"
            "Use this tool when:\n"
            "- The user asks what documents are available\n"
            "- You need to discover valid document identifiers\n"
            "- You want to prepare a call to search_by_document\n"
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_tags",
        "description": (
            "Return all unique tags used across the knowledge base.\n\n"
            "Use this tool when:\n"
            "- You need to discover available business domains (e.g. compliance, onboarding, HR, product)\n"
            "- You want to filter results using search_by_tag but do not know which tags exist\n\n"
            "Do NOT guess tags. Always call this tool first if unsure."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "search",
        "description": (
            "Run semantic search across the entire knowledge base.\n\n"
            "This is the default search tool.\n\n"
            "Use this tool when:\n"
            "- The query is general or exploratory\n"
            "- You do not know which tags or documents to filter by\n\n"
            "Arguments:\n"
            "- query (required): the user question or search query\n"
            "- limit (optional): number of results to return\n"
            "- min_score (optional): filter out weak matches\n"
        ),
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
        "description": (
            "Run semantic search restricted to one or more tags.\n\n"
            "Use this tool ONLY when you already know which tags are relevant.\n\n"
            "Use this tool when:\n"
            "- The user clearly refers to a business domain (e.g. compliance, onboarding, HR, product)\n"
            "- You already obtained valid tags from list_tags\n\n"
            "DO NOT use this tool if tags are unknown.\n"
            "If unsure, call list_tags first or use search instead.\n\n"
            "Arguments:\n"
            "- query (required): the search query\n"
            "- tags (required): list of tags to filter results\n"
            "- limit (optional): number of results\n"
            "- min_score (optional): filter weak matches\n"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "limit": {"type": "integer"},
                "min_score": {"type": "number"},
            },
            "required": ["query", "tags"],
        },
    },
    {
        "name": "search_by_document",
        "description": (
            "Run semantic search restricted to specific documents.\n\n"
            "Use this tool when:\n"
            "- The user mentions a specific document\n"
            "- You need to compare or extract information from known documents\n"
            "- You already obtained document identifiers from list_documents\n\n"
            "Arguments:\n"
            "- query (required): the search query\n"
            "- document_identifiers (required): list of document IDs or filenames\n"
            "- limit (optional): number of results\n"
            "- min_score (optional): filter weak matches\n"
        ),
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