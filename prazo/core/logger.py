import logging
from typing import Any, Dict

from langchain_core.callbacks import BaseCallbackHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ConsoleToolLogger(BaseCallbackHandler):
    """Logs tool calls to console for real-time monitoring."""

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Print when a tool is being called."""
        tool_name = serialized.get("name", "Unknown Tool")
        print(f"\n🔧 Tool Called: {tool_name}")
        print(
            f"   Input: {input_str[:150]}{'...' if len(input_str) > 150 else ''}"
        )

    def on_tool_end(
        self,
        output: str,
        **kwargs: Any,
    ) -> None:
        """Print when a tool call completes."""
        output_str = str(output)
        print(
            f"✅ Tool Completed - Output length: {len(output_str)} characters"
        )

    def on_tool_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Print when a tool call errors."""
        print(f"❌ Tool Error: {str(error)}")
