from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from prazo.core.config import config


class ChatModel:
    def __init__(
        self,
        provider: str,
        model_name: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs

    def llm(self) -> BaseChatModel:
        model_kwargs = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            **self.kwargs,
        }
        if self.provider == "openai":
            return ChatOpenAI(
                model=self.model_name,
                **model_kwargs,
                api_key=config.OPENAI_API_KEY,
            )
        elif self.provider == "google":
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                **model_kwargs,
                api_key=config.GEMINI_API_KEY,
            )
        elif self.provider == "deepseek":
            return ChatDeepSeek(
                model=self.model_name,
                **model_kwargs,
                api_key=config.DEEPSEEK_API_KEY,
            )
        else:
            raise ValueError(f"Invalid provider: {self.provider}")
