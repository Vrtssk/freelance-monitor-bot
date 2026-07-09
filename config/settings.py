from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str = ""
    ALLOWED_USER_IDS: str = ""
    DB_PATH: str = "data/bot.db"
    SCRAPE_INTERVAL: int = 300

    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"

    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )

    @property
    def allowed_users(self) -> set[int] | None:
        if not self.ALLOWED_USER_IDS.strip():
            return None
        return {int(x.strip()) for x in self.ALLOWED_USER_IDS.split(",") if x.strip()}


settings = Settings()
