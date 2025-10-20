"""Tools to summarise news articles"""
from abc import ABC, abstractmethod

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
        pass
    
    def summarise(self, text: str) -> str:
        pass
    
class GeminiSummaryTool(BaseSummaryTool):
    def __init__(self):
        pass
    
    def summarise(self, text: str) -> str:
        pass
        