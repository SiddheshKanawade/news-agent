from typing import Dict

from langchain_core.tools import BaseTool
from pydantic import Field

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
    description: str = (
        "Service for fetching news articles from different news channels like BBC, NDTV Profit, NY Times etc. Tool ensures that the news articles are latest and not already processed."
    )

    # Define source_config_map as a Pydantic field
    source_config_map: Dict[Source, SourceConfig] = Field(
        default_factory=lambda: SOURCE_CONFIG_MAP,
        description="Mapping of sources to their configurations",
    )

    class Config:
        """Pydantic configuration"""

        arbitrary_types_allowed = True

    def summarise(self, articles: list[Article]) -> list[Article]:
        return articles

    def fetch_and_parse(self) -> list[Article]:
        articles = []
        for _, source_config in self.source_config_map.items():
            try:
                source_articles = source_config.parse()
                articles.extend(source_articles)
            except Exception as e:
                logger.error(
                    f"Error fetching and parsing {source_config.source}: {e}"
                )
        return articles

    def _run(self, **kwargs) -> list[Article]:
        return self.fetch_and_parse()
