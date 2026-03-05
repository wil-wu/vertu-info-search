import logging
from typing import Union

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, Field

from meilisearch import Client

logger = logging.getLogger(__name__)


class SearchParams(BaseModel):
    keyword: str = Field(
        description="模糊搜索词，如'agent q 白色'。如果没有则为空字符串"
    )
    filter: list[Union[str, list[str]]] = Field(
        description="精准过滤条件数组，支持 Meilisearch 语法"
    )


class SemanticRetriever:
    """
    语义检索器
    """

    def __init__(
        self,
        meili_client: Client,
        llm_client: AsyncOpenAI | OpenAI,
        model: str,
        system_prompt: str,
    ):
        self.meili_client = meili_client
        self.llm_client = llm_client
        self.model = model
        self.system_prompt = system_prompt

    async def retrieve(self, index_name: str, query: str, **kwargs) -> list[dict]:
        """
        Args:
            index_name: 索引名称
            query: 查询语句
            **kwargs: 其他参数

        Returns:
            list[dict]: 检索结果
        """
        index = self.meili_client.index(index_name)

        try:
            response = await self.llm_client.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": query},
                ],
                response_format=self._build_response_format(),
            )
            search_params = response.choices[0].message.parsed
        except Exception as e:
            logger.error(f"query parsing error: {e}")
            search_params = SearchParams(keyword=query, filter=[])
        
        logger.info(f"query: {query}")
        logger.info(f"search_params: {search_params}")

        return index.search(
            search_params.keyword,
            {
                "filter": search_params.filter,
                **kwargs,
            },
        )

    def _build_response_format(self) -> BaseModel:
        return SearchParams
