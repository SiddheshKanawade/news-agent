"""LLM tool calling"""

from typing import Literal, Optional, Union

from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
from langchain_community.tools.reddit_search.tool import RedditSearchRun
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.utilities.reddit_search import RedditSearchAPIWrapper
from langchain_tavily import TavilySearch

from prazo.core.config import config
from prazo.utils.db import DatabaseAPIWrapper, DatabaseCheckRun
from prazo.utils.search.ddg_search import DDGSearchTool


def tavily_search_tool(
    max_results: int = 5,
    topic: Literal["general", "news"] = "general",
    include_domains: list[str] = [],
    exclude_domains: list[str] = [],
    days: int = 7,
    time_range: Optional[
        Literal["day", "week", "month", "year", "d", "w", "m", "y"]
    ] = None,
    auto_parameters: bool = False,
    search_depth: Literal["basic", "advanced"] = "basic",
    chunks_per_source: int = 3,
    include_images: bool = False,
    include_image_descriptions: bool = False,
    include_answer: Union[bool, Literal["basic", "advanced"]] = False,
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


def wikipedia_search_tool(
    top_k_results: int = 3, doc_content_chars_max: int = 4000, lang: str = "en"
):
    api_wrapper = WikipediaAPIWrapper(
        top_k_results=top_k_results,
        doc_content_chars_max=doc_content_chars_max,
        lang=lang,
    )
    return WikipediaQueryRun(api_wrapper=api_wrapper)


def arxiv_search_tool(
    top_k_results: int = 3,
    doc_content_chars_max: int = 4000,
    load_max_docs: int = 5,
):
    api_wrapper = ArxivAPIWrapper(
        top_k_results=top_k_results,
        doc_content_chars_max=doc_content_chars_max,
        load_max_docs=load_max_docs,
        continue_on_failure=True,
    )
    return ArxivQueryRun(api_wrapper=api_wrapper)


def reddit_search_tool():
    api_wrapper = RedditSearchAPIWrapper(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent=config.REDDIT_USER_AGENT,
    )
    return RedditSearchRun(api_wrapper=api_wrapper)


def ddg_search_tool():
    return DDGSearchTool()


def database_check_tool():
    """
    Create a database URL check tool.

    This tool checks if URLs already exist in the database to avoid duplicate processing.
    Use this before processing news items to verify which URLs are already in the database.

    Returns:
        DatabaseCheckRun: Tool instance for checking URL existence
    """
    api_wrapper = DatabaseAPIWrapper()
    return DatabaseCheckRun(api_wrapper=api_wrapper)
