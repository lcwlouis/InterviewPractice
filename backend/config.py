from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    interview_provider: str = Field(default='openai', alias='INTERVIEW_PROVIDER')
    openai_api_key: str = Field(default='', alias='OPENAI_API_KEY')
    openai_model: str = Field(default='gpt-4.1-mini', alias='OPENAI_MODEL')
    gemini_api_key: str = Field(default='', alias='GEMINI_API_KEY')
    gemini_model: str = Field(default='gemini-2.5-pro', alias='GEMINI_MODEL')
    gemini_live_model: str = Field(default='gemini-2.0-flash-live-001', alias='GEMINI_LIVE_MODEL')
    app_log_level: str = Field(default='INFO', alias='APP_LOG_LEVEL')
    enable_web_research: bool = Field(default=False, alias='ENABLE_WEB_RESEARCH')
    default_country_preset: str = Field(default='SG', alias='DEFAULT_COUNTRY_PRESET')
    search_api_key: str = Field(default='', alias='SEARCH_API_KEY')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
