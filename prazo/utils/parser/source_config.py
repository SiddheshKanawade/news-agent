from enum import Enum

from prazo.utils.parser.helper import get_latest_sitemap

from .parser_tools import BaseParserTool, NDTVProfitParserTool


class Source(Enum):
    """
    Mapping between source name and its identifier
    """

    BBC = "bbc"
    NDTV_PROFIT = "ndtv_profit"
    NY_TIMES = "ny_times"


class SourceConfig:
    """Mapping between source name and its configuration"""

    source: Source
    sitemap_url: str
    parser_tool: BaseParserTool
    filter_kwargs: dict

    def __init__(
        self,
        source: Source,
        sitemap_url: str,
        parser_tool: BaseParserTool,
        filter_kwargs: dict,
    ):
        self.source = source
        self.sitemap_url = sitemap_url
        self.parser_tool = parser_tool(sitemap_url)
        self.filter_kwargs = filter_kwargs

    def parse(self) -> list[str]:
        return self.parser_tool.parse(**self.filter_kwargs)


# Source configuration map
SOURCE_CONFIG_MAP = {
    # Source.BBC: SourceConfig(
    #     source=Source.BBC,
    #     sitemap_url="https://www.bbc.com/sitemap.xml",
    #     parser_tool=BBCParserTool,
    #     filter_kwargs={},
    # ),
    Source.NDTV_PROFIT: SourceConfig(
        source=Source.NDTV_PROFIT,
        sitemap_url=get_latest_sitemap(
            "https://www.ndtvprofit.com/sitemap.xml"
        ),
        parser_tool=NDTVProfitParserTool,
        filter_kwargs={},
    ),
    # Source.NY_TIMES: SourceConfig(
    #     source=Source.NY_TIMES,
    #     sitemap_url="https://www.nytimes.com/sitemap.xml",
    #     parser_tool=NYTimesParserTool,
    #     filter_kwargs={},
    # ),
}
