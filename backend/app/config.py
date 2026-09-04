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
    # Defaults re-verified 2026-09-04: PPIO delisted the qwen2.5 family and
    # qwen3-next-80b; 235b-a22b-instruct is the non-thinking successor
    # (1.7s short-copy latency, finish=stop). Thinking-model candidates
    # (glm-flash/minimax/kimi) burn max_tokens on reasoning — unusable for
    # the quick tier.
    LLM_QUICK_MODEL: str = "qwen/qwen3-235b-a22b-instruct-2507"
    LLM_STRONG_MODEL: str = "deepseek/deepseek-v4-pro"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    REPORT_RECIPIENT: str = ""

    SCHEDULER_ENABLED: bool = True


settings = Settings()
