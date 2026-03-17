from openai import AsyncOpenAI

from app.core.shared import meili_client
from .config import semantic_search_settings
from .utils import SemanticRetriever
from .prompts import QUERY_PARSING_PROMPT

openai_async_client = AsyncOpenAI(
    base_url=semantic_search_settings.llm_base_url,
    api_key=semantic_search_settings.llm_api_key,
)

semantic_retriever = SemanticRetriever(
    meili_client=meili_client,
    llm_client=openai_async_client,
    model=semantic_search_settings.llm_model,
    system_prompt=QUERY_PARSING_PROMPT,
    use_json_mode=semantic_search_settings.use_json_mode,
)
