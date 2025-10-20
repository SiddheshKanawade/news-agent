from abc import ABC, abstractmethod
import advertools as adv
import pandas as pd
from trafilatura import fetch_url, extract


class BaseParserTool(ABC):
    def __init__(self, sitemap_url: str):
        self.sitemap_url = sitemap_url
    
    @abstractmethod
    def filter_urls(self, url_df: pd.DataFrame, **kwargs) -> list[str]:
        pass 

    @abstractmethod
    def parse(self, **filter_kwargs) -> list[str]:
        url_df = adv.sitemap_to_df(self.sitemap_url)
        return url_df
    
    def extract_text(self, url: str) -> str:
        html = fetch_url(url)
        text = extract(html)
        return text
    
class BBCParserTool(BaseParserTool):
    def __init__(self, sitemap_url: str):
        super().__init__(sitemap_url)
        
    def filter_urls(self, url_df: pd.DataFrame, **kwargs) -> list[str]:
        return url_df['loc'].tolist()
    
    def parse(self, **filter_kwargs) -> list[str]:
        url_df = super().parse(**filter_kwargs)  
        return self.filter_urls(url_df, **filter_kwargs)  
    
class NDTVProfitParserTool(BaseParserTool):
    def __init__(self, sitemap_url: str):
        super().__init__(sitemap_url)
    
    def filter_urls(self, url_df: pd.DataFrame, **kwargs) -> list[str]:
        return url_df['loc'].tolist()
    
    def parse(self, **filter_kwargs) -> list[str]:
        url_df = super().parse(**filter_kwargs)
        return self.filter_urls(url_df, **filter_kwargs)
    
class NYTimesParserTool(BaseParserTool):
    def __init__(self, sitemap_url: str):
        super().__init__(sitemap_url)
    
    def filter_urls(self, url_df: pd.DataFrame, **kwargs) -> list[str]:
        return url_df['loc'].tolist()
    
    def parse(self, **filter_kwargs) -> list[str]:
        url_df = super().parse(**filter_kwargs)
        return self.filter_urls(url_df, **filter_kwargs)