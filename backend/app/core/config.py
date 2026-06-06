"""Application configuration, loaded from environment / .env."""
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Insecure defaults that are fine for dev but must never reach production.
_DEFAULT_JWT_SECRET = "change-me-in-production-please-use-a-long-random-string"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    APP_NAME: str = "MarketPulse"
    ENV: Literal["dev", "test", "prod"] = "dev"
    API_V1_PREFIX: str = "/api/v1"
    # Comma-separated origins; "*" allows all (dev only).
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg://marketpulse:marketpulse@localhost:5432/marketpulse"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    # Run Celery tasks inline (no broker) — handy for tests and small dev setups.
    CELERY_TASK_ALWAYS_EAGER: bool = False

    # --- Security ---
    JWT_SECRET_KEY: str = _DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # --- LLM ---
    LLM_PROVIDER: Literal["groq", "mock"] = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    LLM_MAX_CHARS: int = 1200
    LLM_REQUEST_DELAY_SECONDS: float = 3.0
    LLM_MAX_RETRIES: int = 5
    # Safety gate: real LLM calls only fire when this is true.
    ALLOW_REAL_LLM: bool = False

    # --- Storage ---
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_LOCAL_DIR: str = "./data/uploads"
    # Max accepted upload size (bytes). Guards against memory-exhaustion DoS on the
    # unauthenticated upload endpoint. Default 25 MiB — generous for a news CSV.
    MAX_UPLOAD_BYTES: int = 25 * 1024 * 1024

    # --- Seeding ---
    NSE_COMPANIES_CSV: str = "./seeds/data/nse_companies.csv"
    # Bootstrap admin created by the user seeder when the users table is empty.
    ADMIN_EMAIL: str = "admin@marketpulse.local"
    ADMIN_PASSWORD: str = "admin12345"
    GROUND_TRUTH_CSV: str = "./seeds/data/ground_truth_seed.csv"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def _guard_prod_secrets(self) -> "Settings":
        """Refuse to boot in production with insecure defaults.

        A committed default JWT secret means anyone can forge tokens, and ``*``
        CORS with credentials is a cross-site request forgery hole. These are fine
        in dev but disqualifying in prod, so fail fast rather than silently ship
        them."""
        if self.ENV != "prod":
            return self
        problems: list[str] = []
        if self.JWT_SECRET_KEY == _DEFAULT_JWT_SECRET:
            problems.append("JWT_SECRET_KEY is still the committed default")
        if len(self.JWT_SECRET_KEY) < 32:
            problems.append("JWT_SECRET_KEY must be at least 32 chars")
        if self.CORS_ORIGINS.strip() == "*":
            problems.append('CORS_ORIGINS="*" is unsafe with credentialed requests')
        if problems:
            raise ValueError(
                "Insecure configuration for ENV=prod: " + "; ".join(problems)
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
