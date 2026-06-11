"""Application settings loaded from backend/.env (see .env.example for the full schema)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str

    IMAGE_PROVIDER: str = "mock"  # 'mock' (fallback, copies style cover) | 'seedream' (real AI via PPIO)

    PPIO_API_KEY: str = ""
    PPIO_BASE_URL: str = "https://api.ppio.com/openai"
    LLM_QUICK_MODEL: str = "qwen/qwen2.5-7b-instruct"
    LLM_STRONG_MODEL: str = "deepseek/deepseek-v3.1"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    REPORT_RECIPIENT: str = ""

    SCHEDULER_ENABLED: bool = True


settings = Settings()
