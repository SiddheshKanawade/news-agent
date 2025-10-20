from abc import ABC, abstractmethod
from datetime import datetime

import advertools as adv
import pandas as pd
from trafilatura import extract, fetch_url

from prazo.schemas.article import Article


class BaseParserTool(ABC):
    def __init__(self, sitemap_url: str):
        self.sitemap_url = sitemap_url

    def extract_text(self, url: str) -> str:
        try:
            html = fetch_url(url)
            text = extract(html)
            return text.strip()
        except Exception as e:
            raise Exception(f"Text extraction failed: {str(e)}")

    @abstractmethod
    def filter_urls(self, url_df: pd.DataFrame, **kwargs) -> list[str]:
        pass

    @abstractmethod
    def parse(self, **filter_kwargs) -> list[Article]:
        url_df = adv.sitemap_to_df(self.sitemap_url)
        return url_df


class BBCParserTool(BaseParserTool):
    def __init__(self, sitemap_url: str):
        super().__init__(sitemap_url)

    def filter_urls(self, url_df: pd.DataFrame, **kwargs) -> list[str]:
        return url_df["loc"].tolist()

    def parse(self, **filter_kwargs) -> list[Article]:
        url_df = super().parse(**filter_kwargs)
        articles = []
        for _, row in url_df.iterrows():
            url = row["loc"]
            source = "BBC"
            published_date = row["lastmod"]
            assert isinstance(
                published_date, datetime
            ), "Published date in BBC sitemap is not a datetime object"
            content = self.extract_text(url)
            # summary = SummaryService().summarise(content) # Generate summary after deduplication
            articles.append(
                Article(
                    url=url,
                    content=content,
                    source=source,
                    published_date=published_date,
                    updated_date=datetime.now(),
                )
            )
        return articles


class NDTVProfitParserTool(BaseParserTool):
    def __init__(self, sitemap_url: str):
        super().__init__(sitemap_url)

    def filter_urls(self, url_df: pd.DataFrame, **kwargs) -> list[str]:
        return url_df["loc"].tolist()

    def parse(self, **filter_kwargs) -> list[Article]:
        url_df = super().parse(**filter_kwargs)
        articles = []
        for _, row in url_df.iterrows():
            url = row["loc"]
            image_url = row["image_loc"]
            source = "NDTV Profit"
            published_date = row["lastmod"]
            assert isinstance(
                published_date, datetime
            ), "Published date in NDTV Profit sitemap is not a datetime object"
            content = self.extract_text(url)
            articles.append(
                Article(
                    url=url,
                    content=content,
                    source=source,
                    image_url=image_url,
                    published_date=published_date,
                    updated_date=datetime.now(),
                )
            )
        return articles


class NYTimesParserTool(BaseParserTool):
    def __init__(self, sitemap_url: str):
        super().__init__(sitemap_url)

    def filter_urls(self, url_df: pd.DataFrame, **kwargs) -> list[str]:
        return url_df["loc"].tolist()

    def parse(self, **filter_kwargs) -> list[Article]:
        url_df = super().parse(**filter_kwargs)
        return self.filter_urls(url_df, **filter_kwargs)
