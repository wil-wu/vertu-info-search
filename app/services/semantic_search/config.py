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

    # llm 配置
    llm_base_url: str = Field(default="", description="LLM 基础 URL")
    llm_api_key: str = Field(default="", description="LLM API 密钥")
    llm_model: str = Field(default="", description="LLM 模型")
    llm_temperature: float = Field(default=0.1, description="LLM 温度")


semantic_search_settings = SemanticSearchSettings()
