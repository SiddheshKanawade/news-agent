from datetime import datetime

from pydantic import BaseModel, Field


class Article(BaseModel):
    url: str
    title: str = Field(default="")
    content: str  # Raw content of the article returned by trafilatura
    summary: str = Field(default="")
    source: str = Field(default="")
    image_url: str = Field(default="")
    published_date: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(default_factory=datetime.now)
