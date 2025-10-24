import html
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime

import advertools as adv
import pandas as pd
import requests
import yaml
from trafilatura import extract, fetch_url
from trafilatura.settings import use_config

from prazo.core.config import config
from prazo.core.db import check_urls_exist
from prazo.core.logger import logger
from prazo.schemas import NewsItem
from prazo.schemas.article import Article
from prazo.utils.chat_models import ChatModel


class BaseParserTool(ABC):
    def __init__(self, sitemap_url: str):
        self.sitemap_url = sitemap_url

    def load_source_yaml(self, source_yaml: str = config.SOURCES_FILE) -> dict:
        with open(source_yaml, "r") as file:
            return yaml.safe_load(file)

    def extract_text(self, url: str) -> str:
        try:
            # Configure trafilatura with custom settings
            newconfig = use_config()
            newconfig.set("DEFAULT", "MAX_REDIRECTS", "5")

            # First try with trafilatura's fetch_url
            try:
                html = fetch_url(url, config=newconfig)
                if html:
                    text = extract(html, config=newconfig)
                    if text:
                        return text.strip()
            except Exception as fetch_error:
                logger.warning(
                    f"Trafilatura fetch failed, trying requests library: {str(fetch_error)}"
                )

            # Fallback to requests library with custom settings
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                allow_redirects=True,
                max_redirects=5,
            )
            response.raise_for_status()

            # Extract text using trafilatura
            text = extract(response.text, config=newconfig)
            if text:
                return text.strip()

            logger.warning(f"No text extracted from url: {url}")
            return None

        except requests.exceptions.TooManyRedirects:
            logger.error(f"Too many redirects for url: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)} for url: {url}")
            return None
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)} for url: {url}")
            return None

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
        source_data = self.load_source_yaml()
        include = source_data["ndtv_profit"]["include"]
        filtered_df = url_df[
            url_df["loc"].apply(lambda x: x.split("/")[3] in include)
        ]
        return filtered_df
    
    def get_title_from_url(self, url):
        try:
            title = url.split("/")[-1].replace("-", " ").title()
            return title
        except Exception as e:
            logger.error(f"Error getting title: {e} for url: {url}")
            return None
    
    def get_title_from_image_caption(self, html_text: str) -> str | None:
        try:
            matches = re.findall(
                r"<p[^>]*>(.*?)</p>", html_text, flags=re.DOTALL
            )

            if not matches:
                return None

            # Decode HTML entities like &nbsp; and strip whitespace
            paragraph = html.unescape(matches[0].strip())

            # Split on '.' and return the first part
            first_sentence = paragraph.split(".")[0].strip()

            return first_sentence or None
        except Exception as e:
            logger.error(f"Error getting title: {e} for html_text: {html_text}")
            return None

    def get_title(self, html_text: str, url: str) -> str | None:
        try:
            title = self.get_title_from_url(url)
            if title is None:
                title = self.get_title_from_image_caption(html_text)
            return title
        except Exception as e:
            logger.error(f"Error getting title: {e} for url: {url}")
            return None

    def summarise_article(self, content: str) -> str:
        llm = ChatModel(provider="openai", model_name="gpt-4o-mini").llm()
        prompt = f"""
        You are a summariser.
        Summarise the following content in 1-2 paragraphs about 100-150 words:
        {content}
        Return your response in this exact format:
        SUMMARY: [summary]
        """
        response = llm.invoke(prompt)
        content = response.content.strip()
        lines = content.split("\n")
        summary = ""
        for line in lines:
            line = line.strip()
            if line.startswith("SUMMARY:"):
                summary = line.replace("SUMMARY:", "").strip()
        return summary

    def parse(self, **filter_kwargs) -> list[NewsItem]:
        url_df = super().parse(**filter_kwargs)
        url_df = self.filter_urls(url_df, **filter_kwargs)
        articles = []
        for _, row in url_df.iterrows():
            url = row["loc"]
            try:
                title = self.get_title(row["image_caption"], url)
                if title is None:
                    title = "Untitled"
                published_date = row["lastmod"]
                assert isinstance(
                    published_date, datetime
                ), "Published date in NDTV Profit sitemap is not a datetime object"

                # Check if URL already exists before extracting content
                existing_urls = check_urls_exist([url])
                if len(existing_urls) > 0:
                    logger.info(f"Skipping existing URL: {url}")
                    continue

                content = self.extract_text(url)

                articles.append(
                    NewsItem(
                        title=title,
                        summary=(
                            self.summarise_article(content)
                            if content is not None
                            else "No content found"
                        ),
                        sources=[url],
                        published_date=published_date,
                        topic=["NDTV Profit", url.split("/")[3]],
                        groups=["NDTV Profit"],
                        tool_source=["daily_news"],
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                )
                time.sleep(1)

            except Exception as e:
                logger.error(f"Failed to parse article from {url}: {str(e)}")
                continue

        logger.info(
            f"Successfully parsed {len(articles)} articles from NDTV Profit"
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
