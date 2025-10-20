from summary_tools import (
    BaseSummaryTool,
    DeepSeekSummaryTool,
    GeminiSummaryTool,
    OpenAISummaryTool,
)


class SummaryService:
    def __init__(self, tool: str = "deepseek"):
        self.tool = self._get_tool(tool)

    def _get_tool(self, tool: str) -> BaseSummaryTool:
        if tool == "deepseek":
            return DeepSeekSummaryTool()
        elif tool == "gemini":
            return GeminiSummaryTool()
        elif tool == "openai":
            return OpenAISummaryTool()
        else:
            raise ValueError(f"Invalid tool: {tool}")

    def summarise(self, text: str) -> str:
        return self.tool.summarise(text)
