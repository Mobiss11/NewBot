from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str
    openrouter_api_key: str
    openrouter_model: str = "google/gemini-2.5-flash-lite"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    database_url: str = "sqlite+aiosqlite:///./data/bot.db"

    short_term_limit: int = 10
    fact_extraction_interval: int = 4
    max_facts_per_avatar: int = 20

    stream_edit_interval: float = 1.0

    log_level: str = "INFO"


settings = Settings()  # type: ignore[call-arg]
