"""
Nexora AI — Web Search Router
Real-time internet access via DuckDuckGo (free) or Tavily (premium).
"""

import time
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.models.user import User
from app.schemas.schemas import WebSearchRequest, WebSearchResponse, SearchResult
from app.middleware.auth_middleware import get_current_user
from app.config import settings

router = APIRouter()


async def search_duckduckgo(query: str, num_results: int = 10) -> list[SearchResult]:
    """Free web search using DuckDuckGo."""
    from duckduckgo_search import DDGS

    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=num_results):
            results.append(SearchResult(
                title=r.get("title", ""),
                url=r.get("href", ""),
                snippet=r.get("body", ""),
                source="duckduckgo",
            ))
    return results


async def search_tavily(query: str, num_results: int = 10) -> list[SearchResult]:
    """Premium search using Tavily API — better quality, more context."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    response = client.search(
        query=query,
        max_results=num_results,
        include_answer=True,
        include_raw_content=False,
    )
    results = []
    for r in response.get("results", []):
        results.append(SearchResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("content", ""),
            source="tavily",
            published_date=r.get("published_date"),
        ))
    return results


@router.post("/", response_model=WebSearchResponse)
async def web_search(
    payload: WebSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Search the web and return structured results.
    Uses Tavily if API key is configured, falls back to DuckDuckGo.
    """
    start_ms = int(time.time() * 1000)

    if settings.TAVILY_API_KEY:
        results = await search_tavily(payload.query, payload.num_results)
        source = "tavily"
    else:
        results = await search_duckduckgo(payload.query, payload.num_results)
        source = "duckduckgo"

    elapsed = int(time.time() * 1000) - start_ms

    return WebSearchResponse(
        query=payload.query,
        results=results,
        total_results=len(results),
        search_time_ms=elapsed,
    )


@router.get("/quick")
async def quick_search(
    q: str = Query(..., min_length=1, max_length=500),
    n: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
):
    """Quick GET endpoint for simple web search queries."""
    if settings.TAVILY_API_KEY:
        results = await search_tavily(q, n)
    else:
        results = await search_duckduckgo(q, n)

    return {
        "query": q,
        "results": [r.model_dump() for r in results],
    }