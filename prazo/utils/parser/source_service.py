from langchain_core.tools import BaseTool

from prazo.core.logger import logger
from prazo.schemas.article import Article
from prazo.utils.parser.source_config import (
    SOURCE_CONFIG_MAP,
    Source,
    SourceConfig,
)


class SourceService(BaseTool):
    """Service for fetching and parsing sources"""

    name: str = "fetch_and_parse_sources"
    description: str = f"Service for fetching news articles from different news channels like BBC, NDTV Profit, NY Times etc. Tool ensures that the news articles are latest and not already processed."

    def __init__(
        self, source_config_map: dict[Source, SourceConfig] = SOURCE_CONFIG_MAP
    ):
        self.source_config_map = source_config_map

    def fetch_and_parse(self) -> list[Article]:
        articles = []
        for _, source_config in self.source_config_map.items():
            try:
                articles = source_config.parse()
                articles.extend(articles)
            except Exception as e:
                logger.error(
                    f"Error fetching and parsing {source_config.source}: {e}"
                )
        return articles

    def _run(self, **kwargs) -> list[Article]:
        return self.fetch_and_parse()

    def _arun(self, **kwargs) -> list[Article]:
        return self.fetch_and_parse()
