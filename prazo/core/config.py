import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Config(BaseModel):
    """Configuration settings for the autodub service"""

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")

    def validate_api_keys(self):
        """Validate that required API keys are set."""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        if not self.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
        if not self.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY environment variable is not set")

class ProductionConfig(Config):
    """Production configuration settings for the news agent"""


class StagingConfig(Config):
    """Staging configuration settings for the news agent"""


class LocalConfig(Config):
    """Local configuration settings for the news agent"""


def get_config():
    env = os.getenv("ENV", "local")
    config_type = {
        "local": LocalConfig(),
        "staging": StagingConfig(),
        "production": ProductionConfig(),
    }
    return config_type[env]


# Global config instance
config: Config = get_config()
config.validate_api_keys()
