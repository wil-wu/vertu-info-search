from fastapi import APIRouter, HTTPException
from meilisearch.errors import MeilisearchApiError

from app.core.shared import meili_client
from .models import ProductSearchRequest, ProductSearchResponse
from .config import semantic_search_settings
from .shared import semantic_retriever

router = APIRouter(prefix="/api/v1/semantic", tags=["semantic_search"])


@router.post("/product/search", response_model=ProductSearchResponse)
async def product_search(request: ProductSearchRequest) -> ProductSearchResponse:
    try:
        meili_client.get_index(request.index_name)
    except MeilisearchApiError:
        raise HTTPException(
            status_code=404, detail=f"Index {request.index_name} not found"
        )

    result = await semantic_retriever.retrieve(
        request.index_name,
        request.query,
        showRankingScore=semantic_search_settings.show_ranking_score,
        page=request.page,
        hitsPerPage=request.hits_per_page,
    )

    return ProductSearchResponse(
        hits=result["hits"],
        page=result["page"],
        hits_per_page=result["hitsPerPage"],
        total_pages=result["totalPages"],
        total_hits=result["totalHits"],
    )
