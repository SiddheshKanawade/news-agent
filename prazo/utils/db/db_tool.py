"""Database tool for checking URL existence."""

from typing import Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from prazo.utils.db.db_wrapper import DatabaseAPIWrapper


class DatabaseCheckInput(BaseModel):
    """Input schema for database URL check tool."""

    query: str = Field(
        description="Comma-separated list of URLs to check against the database. Example: 'https://example.com/article1, https://example.com/article2'"
    )


class DatabaseCheckRun(BaseTool):
    """Tool for checking if URLs already exist in the database."""

    name: str = "database_url_check"
    description: str = (
        "Check if URLs already exist in the database to avoid duplicate processing. "
        "Use this tool before creating news items to verify which URLs are already processed. "
        "Input should be a comma-separated list of URLs. "
        "Returns which URLs exist in the database (should be skipped) and which are new (should be processed)."
    )
    args_schema: Type[BaseModel] = DatabaseCheckInput
    api_wrapper: DatabaseAPIWrapper = Field(default_factory=DatabaseAPIWrapper)

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        return self.api_wrapper.run(query)

