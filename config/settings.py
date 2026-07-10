from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str = ""
    ALLOWED_USER_IDS: str = ""

    DATABASE_URL: str = "postgresql+asyncpg://freelance:freelance@localhost:5432/freelance_bot"

    SCRAPE_INTERVAL: int = 300
    SCRAPE_ENABLED: bool = True
    USE_PLAYWRIGHT: bool = True

    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "poolside/laguna-xs-2.1:free"
    LLM_ENABLED: bool = True

    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    @property
    def allowed_users(self) -> set[int] | None:
        if not self.ALLOWED_USER_IDS.strip():
            return None
        return {int(x.strip()) for x in self.ALLOWED_USER_IDS.split(",") if x.strip()}


settings = Settings()
