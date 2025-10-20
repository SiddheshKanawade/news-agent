"""LLM tool calling"""
from langchain_tavily import TavilySearch
from typing import Literal, Optional, Union

from prazo.core.config import config


def tavily_search_tool(
    max_results: int = 5,
    topic: Literal['general', 'news'] = 'general',
    include_domains: list[str] = [],
    exclude_domains: list[str] = [],
    days: int = 7,
    time_range: Optional[Literal['day', 'week', 'month', 'year', 'd', 'w', 'm', 'y']] = None,
    auto_parameters: bool = False,
    search_depth: Literal['basic', 'advanced'] = 'basic',
    chunks_per_source: int = 3,
    include_images: bool = False,
    include_image_descriptions: bool = False,
    include_answer: Union[bool, Literal['basic', 'advanced']] = False,
    country: Optional[str] = None,
    timeout: int = 60,
    include_favicon: bool = False,
) -> TavilySearch:
    return TavilySearch(
        tavily_api_key=config.TAVILY_API_KEY,
        max_results=max_results,
        topic=topic,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        days=days,
        time_range=time_range,
        auto_parameters=auto_parameters,
        search_depth=search_depth,
        chunks_per_source=chunks_per_source,
        include_images=include_images,
        include_image_descriptions=include_image_descriptions,
        include_answer=include_answer,
        country=country,
        timeout=timeout,
        include_favicon=include_favicon,
    )