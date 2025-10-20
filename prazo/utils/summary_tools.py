"""Tools to summarise news articles"""

from abc import ABC, abstractmethod

import openai
from core.config import config


class BaseSummaryTool(ABC):
    @abstractmethod
    def summarise(self, text: str) -> str:
        pass


class OpenAISummaryTool(BaseSummaryTool):
    def __init__(self):
        pass

    def summarise(self, text: str) -> str:
        pass


class DeepSeekSummaryTool(BaseSummaryTool):
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=config.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com"
        )

    def summarise(self, text: str) -> str:
        """Summarise the text using the DeepSeek API"""
        # TODO: Add chunking in case text is too long.
        try:
            system_content = (
                f"Attached is a news article text. You are a summariser."
                f"Summarise the attached text"
                f"Keep the summary concise and to the point."
                f"The summary should be in the same language as the text."
                f"Don't include any other information in the summary."
                f"Don't neglect any crucial information."
            )

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": system_content,
                    },
                    {"role": "user", "content": text},
                ],
                timeout=30,  # DeepSeek timeout
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"DeepSeek summarisation failed: {str(e)}")


class GeminiSummaryTool(BaseSummaryTool):
    def __init__(self):
        pass

    def summarise(self, text: str) -> str:
        pass
