from pydantic import BaseModel


class ProductSearchRequest(BaseModel):
    index_name: str
    query: str
    page: int = 1
    hits_per_page: int = 10


class ProductSearchResponse(BaseModel):
    hits: list[dict]
    page: int
    hits_per_page: int
    total_pages: int
    total_hits: int
