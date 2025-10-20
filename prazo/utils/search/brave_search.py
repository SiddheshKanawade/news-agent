import threading

from langchain_community.utilities.brave_search import BraveSearchWrapper
from langchain_core.tools import BaseTool
from pydantic import Field

# Global rate limiter for Brave Search API (1 request per second for free tier)
_brave_search_lock = threading.Lock()
_last_request_time = 0


class BraveSearchTool(BaseTool):
    name: str = "brave_search"
    description: str = (
        "a search engine. "
        "useful for when you need to answer questions about current events."
        " input should be a search query."
    )
    search_wrapper: BraveSearchWrapper = Field(
        default_factory=BraveSearchWrapper
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for rate-limited requests",
    )

    def _run(self, query: str) -> str:
        return self.search(query)

    def search(self, query: str) -> str:
        return self.search(query)
