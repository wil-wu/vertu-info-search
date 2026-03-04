from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SemanticSearchSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SEMANTIC_SEARCH_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # meilisearch 配置
    show_ranking_score: bool = Field(default=True, description="是否显示相关性得分")


semantic_search_settings = SemanticSearchSettings()
