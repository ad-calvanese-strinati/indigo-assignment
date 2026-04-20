from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Indigo Knowledge Base"

    database_url: str = Field(
        default="",
        alias="DATABASE_URL",
    )

    openai_api_key: str = Field(
        default="",
        alias="OPENAI_API_KEY",
    )

    mcp_auth_token: str = Field(
        default="",
        alias="MCP_AUTH_TOKEN",
    )

    # Config opzionali (con default)
    embedding_model: str = Field(
        default="text-embedding-3-small", alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=1536, alias="EMBEDDING_DIMENSION")

    app_allowed_origins_raw: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        alias="APP_ALLOWED_ORIGINS",
    )

    max_chunk_chars: int = Field(default=1200, alias="MAX_CHUNK_CHARS")
    chunk_overlap_chars: int = Field(default=200, alias="CHUNK_OVERLAP_CHARS")

    default_search_limit: int = Field(default=5, alias="DEFAULT_SEARCH_LIMIT")
    max_search_limit: int = Field(default=10, alias="MAX_SEARCH_LIMIT")

    hybrid_candidate_limit: int = Field(default=20, alias="HYBRID_CANDIDATE_LIMIT")
    hybrid_rrf_k: int = Field(default=60, alias="HYBRID_RRF_K")

    min_chunk_characters: int = Field(default=40, alias="MIN_CHUNK_CHARACTERS")
    min_chunk_alpha_characters: int = Field(
        default=12, alias="MIN_CHUNK_ALPHA_CHARACTERS"
    )

    min_dense_score: float = Field(default=0.45, alias="MIN_DENSE_SCORE")
    min_lexical_score: float = Field(default=0.02, alias="MIN_LEXICAL_SCORE")

    embedding_batch_max_inputs: int = Field(
        default=128, alias="EMBEDDING_BATCH_MAX_INPUTS"
    )
    embedding_batch_max_tokens: int = Field(
        default=200000, alias="EMBEDDING_BATCH_MAX_TOKENS"
    )

    model_config = SettingsConfigDict(
        env_file=".env",  # ✔ usato solo in locale
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def app_allowed_origins(self) -> list[str]:
        return [
            item.strip()
            for item in self.app_allowed_origins_raw.split(",")
            if item.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    # Fail fast per config critiche
    if not settings.database_url:
        raise ValueError("DATABASE_URL is required")

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required")

    if not settings.mcp_auth_token:
        raise ValueError("MCP_AUTH_TOKEN is required")

    return settings