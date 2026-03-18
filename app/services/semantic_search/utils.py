import re
import json
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
    sort: list[str] = Field(
        description="排序条件数组，支持 Meilisearch 语法"
    )


class SemanticRetriever:
    """
    语义检索器。支持两种 LLM 调用方式：
    - use_json_mode=True：使用 chat.completions.parse（需 LLM 支持 JSON/structured output）
    - use_json_mode=False：使用普通 completion，从返回文本中解析 JSON（适配不支持 json mode 的 LLM）
    """

    def __init__(
        self,
        meili_client: Client,
        llm_client: AsyncOpenAI | OpenAI,
        model: str,
        system_prompt: str,
        use_json_mode: bool = True,
    ):
        self.meili_client = meili_client
        self.llm_client = llm_client
        self.model = model
        self.system_prompt = system_prompt
        self.use_json_mode = use_json_mode

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
            search_params = await self._parse_query(query)
        except Exception as e:
            logger.error(f"query parsing error: {e}")
            search_params = SearchParams(keyword=query, filter=[], sort=[])

        logger.info(f"query: {query}")
        logger.info(f"search_params: {search_params}")

        return index.search(
            search_params.keyword,
            {
                "filter": search_params.filter,
                "sort": search_params.sort,
                **kwargs,
            },
        )

    async def _parse_query(self, query: str) -> SearchParams:
        """根据 use_json_mode 选择解析方式，返回 SearchParams。"""
        if self.use_json_mode:
            return await self._parse_query_with_json_mode(query)
        return await self._parse_query_from_text(query)

    async def _parse_query_with_json_mode(self, query: str) -> SearchParams:
        """使用 completions.parse 获取结构化输出（需 LLM 支持）。"""
        response = await self.llm_client.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": query},
            ],
            response_format=self._build_response_format(),
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise ValueError("LLM returned null parsed result")
        return parsed

    async def _parse_query_from_text(self, query: str) -> SearchParams:
        """使用普通 completion，从返回文本中解析 JSON（适配不支持 json mode 的 LLM）。"""
        response = await self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": query},
            ],
        )
        content = response.choices[0].message.content
        data = self._parse_json_from_text(content) if content else None
        if data is None:
            raise ValueError(f"Cannot parse JSON from LLM response: {content!r}")
        return SearchParams(**data)
    
    def _parse_json_from_text(self, text: str) -> dict | None:
        """从 LLM 返回的文本中解析 JSON，兼容被 markdown 代码块包裹的情况。"""
        if not text or not text.strip():
            return None
        text = text.strip()
        # 去掉 ```json ... ``` 或 ``` ... ```
        match = re.search(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _build_response_format(self) -> type[BaseModel]:
        return SearchParams
