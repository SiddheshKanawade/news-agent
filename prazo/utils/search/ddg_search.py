import random
import threading
import time

from duckduckgo_search import DDGS
from langchain_core.tools import BaseTool

from prazo.core.logger import logger

_ddg_search_lock = threading.Lock()
_last_ddg_request_time = 0
_ddg_base_delay = 15.0
_ddg_max_retries = 5


class DDGSearchTool(BaseTool):
    name: str = "ddg_search"
    description: str = "Search the web for the latest news articles"

    @staticmethod
    def ddg_tool(
        query: str,
    ) -> list[dict[str, str]]:
        """DuckDuckGo text search generator with robust rate limiting and retry logic.

        Args:
            query: query for search.

        Returns:
            List of dictionaries with search results.
        """
        global _last_ddg_request_time

        USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.81",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux i686; rv:124.0) Gecko/20100101 Firefox/124.0",
        ]

        for attempt in range(_ddg_max_retries):
            with _ddg_search_lock:
                current_time = time.time()
                # Calculate delay (increase after failed attempts)
                current_delay = _ddg_base_delay * (
                    1.5**attempt
                )  # Progressive delay
                time_since_last = current_time - _last_ddg_request_time

                if time_since_last < current_delay:
                    sleep_time = current_delay - time_since_last
                    logger.info(
                        f"DuckDuckGo rate limiting: waiting {sleep_time:.1f} seconds (attempt {attempt + 1}/{_ddg_max_retries})..."
                    )
                    time.sleep(sleep_time)

                try:
                    logger.info(
                        f"DuckDuckGo search: attempting query '{query}' (attempt {attempt + 1}/{_ddg_max_retries})"
                    )
                    res = DDGS(
                        headers={"User-Agent": random.choice(USER_AGENTS)}
                    ).news(query, max_results=10)
                    _last_ddg_request_time = time.time()

                    # Check if we got a rate limit response in the results
                    if isinstance(res, list) and len(res) > 0:
                        # Sometimes rate limit info comes in the response
                        first_result = res[0] if res else {}
                        if any(
                            term in str(first_result).lower()
                            for term in ["ratelimit", "rate limit"]
                        ):
                            raise Exception(
                                "DuckDuckGo rate limit detected in response"
                            )

                    logger.info(
                        f"DuckDuckGo search successful: found {len(res)} results"
                    )
                    return res

                except Exception as e:
                    logger.error(f"Error occured in DDG: {e}")
                    _last_ddg_request_time = time.time()
                    error_msg = str(e).lower()

                    # Check for rate limit related errors
                    if any(
                        term in error_msg
                        for term in [
                            "ratelimit",
                            "rate limit",
                            "202",
                            "too many requests",
                        ]
                    ):
                        if attempt < _ddg_max_retries - 1:
                            # Exponential backoff for rate limit errors
                            backoff_time = (2**attempt) * 5  # 5, 10, 20 seconds
                            logger.info(
                                f"DuckDuckGo rate limit error detected. Backing off for {backoff_time} seconds..."
                            )
                            time.sleep(backoff_time)
                            continue
                        else:
                            logger.info(
                                f"DuckDuckGo: Max retries exceeded due to rate limiting. Error: {e}"
                            )
                            # Return empty results instead of crashing
                            return []
                    else:
                        # Non-rate-limit error, re-raise immediately
                        logger.error(f"DuckDuckGo search error (non-rate-limit): {e}")
                        raise e

        # If we get here, all retries failed due to rate limiting
        logger.error(
            "DuckDuckGo: All retry attempts failed due to rate limiting. Returning empty results."
        )
        return []

    def _run(self, query: str) -> str:
        return self.ddg_tool(query)
