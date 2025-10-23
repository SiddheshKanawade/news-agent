"""Database API Wrapper for checking URL existence."""

from typing import List, Set

from pydantic import BaseModel

from prazo.core.db import check_urls_exist
from prazo.core.logger import logger


class DatabaseAPIWrapper(BaseModel):
    """Wrapper for database URL checking operations."""

    class Config:
        arbitrary_types_allowed = True

    def check_urls(self, urls: List[str]) -> dict:
        """
        Check which URLs from the provided list already exist in the database.

        Args:
            urls: List of URLs to check against the database

        Returns:
            dict: Contains 'existing_urls', 'new_urls', and 'message'
        """
        if not urls:
            return {
                "existing_urls": [],
                "new_urls": [],
                "message": "No URLs provided to check",
            }

        logger.info(f"Checking {len(urls)} URLs against database")

        # Get URLs that exist in database
        existing_urls: Set[str] = check_urls_exist(urls)
        existing_urls_list = list(existing_urls)

        # Get URLs that don't exist (new URLs)
        new_urls = [url for url in urls if url not in existing_urls]

        message = f"Found {len(existing_urls_list)} existing URLs out of {len(urls)} checked"
        logger.info(message)

        return {
            "existing_urls": existing_urls_list,
            "new_urls": new_urls,
            "message": message,
        }

    def run(self, query: str) -> str:
        """
        Run the database check for URLs provided in the query.

        Args:
            query: Comma-separated list of URLs or single URL

        Returns:
            str: Formatted result message
        """
        # Parse URLs from query (comma-separated)
        urls = [url.strip() for url in query.split(",") if url.strip()]

        result = self.check_urls(urls)

        # Format response
        response = f"{result['message']}\n"
        if result["existing_urls"]:
            response += f"\nExisting URLs (skip these):\n"
            for url in result["existing_urls"]:
                response += f"  - {url}\n"

        if result["new_urls"]:
            response += f"\nNew URLs (process these):\n"
            for url in result["new_urls"]:
                response += f"  - {url}\n"

        return response.strip()
