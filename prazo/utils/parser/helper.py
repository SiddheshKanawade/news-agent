import advertools as adv
import pandas as pd


def get_latest_sitemap(base_sitemap:str) -> str:
    url_df = adv.sitemap_to_df(base_sitemap, recursive=False)
    url_df['lastmod'] = pd.to_datetime(url_df['lastmod'], errors='coerce', utc=True) # Normalize timezone and format
    latest_sitemap = url_df.loc[[url_df['lastmod'].idxmax()]].iloc[0]['loc']
    return latest_sitemap