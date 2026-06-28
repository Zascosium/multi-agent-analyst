from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str = ""
    e2b_api_key: str = ""
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"
    max_retries: int = 3
    sandbox_timeout: int = 1800
    model: str = "claude-sonnet-4-6"


settings = Settings()
