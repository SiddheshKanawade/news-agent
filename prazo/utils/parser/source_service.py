from prazo.utils.parser.source_config import SOURCE_CONFIG_MAP, Source, SourceConfig
from prazo.schemas.article import Article

class SourceService:
    """Service for fetching and parsing sources"""

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
                print(f"Error fetching and parsing {source_config.source}: {e}")
        return articles