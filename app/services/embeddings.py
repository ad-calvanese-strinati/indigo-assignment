from fastapi import HTTPException, status
from openai import APIError, AsyncOpenAI, BadRequestError

from app.core.config import get_settings

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    embeddings: list[list[float]] = []
    for batch in _batch_texts(texts):
        try:
            response = await client.embeddings.create(
                model=settings.embedding_model, input=batch
            )
        except BadRequestError as exc:
            message = "The document is too large to embed in its current form."
            if getattr(exc, "body", None):
                api_message = exc.body.get("error", {}).get("message")
                if api_message:
                    message = f"Embedding request rejected: {api_message}"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=message
            ) from exc
        except APIError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The embedding provider returned an unexpected error.",
            ) from exc

        embeddings.extend(item.embedding for item in response.data)

    return embeddings


def _batch_texts(texts: list[str]) -> list[list[str]]:
    batches: list[list[str]] = []
    current_batch: list[str] = []
    current_batch_tokens = 0

    for text in texts:
        estimated_tokens = _estimate_token_count(text)
        would_exceed_inputs = len(current_batch) >= settings.embedding_batch_max_inputs
        would_exceed_tokens = (
            bool(current_batch)
            and current_batch_tokens + estimated_tokens
            > settings.embedding_batch_max_tokens
        )

        if would_exceed_inputs or would_exceed_tokens:
            batches.append(current_batch)
            current_batch = []
            current_batch_tokens = 0

        current_batch.append(text)
        current_batch_tokens += estimated_tokens

    if current_batch:
        batches.append(current_batch)

    return batches


def _estimate_token_count(text: str) -> int:
    # Conservative heuristic for prose: roughly 4 characters per token.
    return max(1, len(text) // 4)
