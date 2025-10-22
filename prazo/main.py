"""Initiate Reactive Agent"""

import asyncio
import json
from typing import List, Literal

import yaml
from langfuse.langchain import CallbackHandler
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command

from prazo.core.config import config
from prazo.core.logger import ConsoleToolLogger, logger
from prazo.schemas import MainNewsAgentState
from prazo.utils.agent.reactive_agent import create_reactive_graph
from prazo.utils.tools import (
    arxiv_search_tool,
    reddit_search_tool,
    tavily_search_tool,
    wikipedia_search_tool,
)


# TODO: Load from YAML file
def get_days_filter_for_groups(groups: List[str]) -> int:
    """Determine the number of days to filter news based on group categories."""
    if any(group.lower() in ["politics"] for group in groups):
        return 2
    elif any(group.lower() in ["technology"] for group in groups):
        return 4
    elif any(group.lower() in ["science"] for group in groups):
        return 7
    elif any(group.lower() in ["health"] for group in groups):
        return 7
    else:
        return 2


def load_topics_data(state: MainNewsAgentState) -> MainNewsAgentState:
    try:
        with open(config.TOPICS_FILE, "r") as file:
            topics_data = yaml.safe_load(file)
        topic_list = list(topics_data.items())  # (key, value) tuple pairs
        return {
            "topics_file": config.TOPICS_FILE,
            "topic_list": topic_list,
            "topic_data": topics_data,
            "current_step": "topics_loaded",
        }
    except Exception as e:
        logger.error(f"Error loading topics data: {e}")
        return {
            "current_step": "topics_loading_failed",
        }


def deduplicate_collections(state: MainNewsAgentState) -> MainNewsAgentState:
    """Deduplicate the collected news items."""
    return {
        "news_collections": state.news_collections,
        "current_step": "collections_deduplicated",
    }


def route_to_next_topic(
    state: MainNewsAgentState,
) -> Command[Literal["process_topic", "deduplicate_collections"]]:
    """Accumulate current news items and decide whether to process next topic or finish."""
    # First, accumulate any current news items from the last topic processing
    updates = {}
    if state.current_news_items:
        updates["news_collections"] = (
            state.news_collections + state.current_news_items
        )
        updates["current_news_items"] = []

    if state.current_topic_index < len(state.topic_list):
        topic_name, topic_info = state.topic_list[state.current_topic_index]
        groups = topic_info.get("groups", [])
        days_filter = get_days_filter_for_groups(groups)

        # Get preferred tools and subreddits from YAML, or use defaults
        preferred_tools = topic_info.get("tools", None)
        subreddits = topic_info.get("subreddits", None)

        # If no tools specified in YAML, fall back to heuristic
        if preferred_tools is None:
            # Heuristic: mark research topics based on keywords in topic or groups
            research_keywords = [
                "research",
                "paper",
                "preprint",
                "arxiv",
                "arXiv",
                "ml",
                "ai",
                "machine learning",
                "deep learning",
                "neural",
                "transformer",
                "nlp",
                "cv",
                "science",
                "biology",
                "physics",
                "math",
                "statistics",
            ]
            topic_l = topic_name.lower()
            group_l = [g.lower() for g in groups]
            is_research_topic = any(
                kw in topic_l for kw in research_keywords
            ) or any(
                kw in g
                for g in group_l
                for kw in [
                    "ai",
                    "ml",
                    "science",
                    "research",
                    "academia",
                ]
            )
            # Default tool selection based on heuristic
            if is_research_topic:
                preferred_tools = ["arxiv", "tavily", "wikipedia"]
            else:
                preferred_tools = ["tavily", "wikipedia"]
        else:
            # Determine is_research_topic based on whether arxiv is in preferred tools
            is_research_topic = "arxiv" in preferred_tools

        if any(group.lower() in ["us", "india", "world"] for group in groups):
            groups += ["breaking news", "politics"]
        groups += ["recent events", "recent developments", "latest news"]

        logger.info(
            f"Processing topic {state.current_topic_index + 1}/{len(state.topic_list)}: {topic_name}"
        )

        updates.update(
            {
                "current_step": f"processing_topic_{state.current_topic_index}",
                "current_topic": topic_name,
                "current_groups": groups,
                "days_filter": days_filter,
                "is_research_topic": is_research_topic,
                "preferred_tools": preferred_tools,
                "subreddits": subreddits,
                "current_topic_index": state.current_topic_index + 1,
            }
        )

        return Command(goto="process_topic", update=updates)
    else:
        logger.info("All topics processed, saving collections")
        updates.update({"current_step": "all_topics_processed"})
        return Command(goto="deduplicate_collections", update=updates)


def save_collections(state: MainNewsAgentState) -> MainNewsAgentState:
    """Save the collected news items to a file."""
    with open(f"collections_{state.current_topic}.json", "w") as file:
        json.dump(
            [item.model_dump(mode="json") for item in state.news_collections],
            file,
            indent=2,
        )
    return {"current_step": "collections_saved"}


def create_news_worker_agent():
    """Create the reactive agent that collects news for a single topic."""

    # Create search tools optimized for recent news
    tavily_tool = tavily_search_tool(
        max_results=8,
        topic="news",
        days=2,
        search_depth="basic",
    )
    wikipedia_tool = wikipedia_search_tool(
        top_k_results=3,
        doc_content_chars_max=4000,
        lang="en",
    )
    arxiv_tool = arxiv_search_tool(
        top_k_results=15,
        doc_content_chars_max=4000,
        load_max_docs=15,
    )
    reddit_tool = reddit_search_tool()
    # Order tools to encourage research-first where applicable
    tools = [arxiv_tool, tavily_tool, wikipedia_tool, reddit_tool]

    system_prompt = """You are a news collection agent. Your task is to collect the latest news articles for the topic "{current_topic}" in the groups {current_groups}.

You must collect {max_items_per_topic} unique news items for each topic. Sort them by relevance and recency.

IMPORTANT: You do NOT need any confirmation for anything. Act autonomously.
Today's date is {today_date}.

IMPORTANT: Only include news from the last {days_filter} days. Filter out any articles older than {days_filter} days from today's date.

=== MANDATORY TOOL USAGE STRATEGY ===

For this topic, you MUST use these tools: {preferred_tools}

Each available tool serves a specific purpose:

**ArXiv Tool** (if available) - Use for research topics:
   - Purpose: Find recent academic papers, preprints, and research developments
   - Query format: Use technical keywords (e.g., "deep learning", "transformers", "reinforcement learning")
   - Make MULTIPLE queries: Try 5-10 different keyword combinations
   - Look for papers from the last {days_filter} days when possible
   
**Tavily Search Tool** (if available) - Use for news:
   - Purpose: Recent news articles and web coverage from the last {days_filter} days
   - Industry announcements, company news, product launches, breaking news
   - Query format: Combine topic + "news", topic + "latest", topic + group keywords
   - Make 5-10 queries with different combinations
   
**Wikipedia Tool** (if available) - Use for context:
   - Purpose: Background context, definitions, understanding entities/concepts
   - Clarifying acronyms, technical terms, historical context
   - Query format: Search for key entities, concepts, or terms (2-3 queries)

**Reddit Tool** (if available) - Use for community discussions:
   - Purpose: Find community discussions, opinions, real-world experiences, and trending topics from POSTS ONLY (not comments)
   - IMPORTANT: When using Reddit, you MUST specify a subreddit from this list: {subreddits}
   - Query format: Use the subreddit parameter with your search query
   - Make 3-5 queries across different subreddits from the list - prefer using reddit for recent posts
   - Sort by "new" or "hot" to find recent discussions
   - ALWAYS use time_filter: "day" to get only posts from the last 24 hours
   - Reddit tool returns POSTS (submissions) only - extract information from post titles and content, NOT from comments
   - LIMIT should be 25 for each query
   - Example query params: {{"query": "your search term", "subreddit": "MachineLearning", "sort": "new", "time_filter": "day", "limit": "25"}}

SEARCH STRATEGY:
If {current_topic} contains multiple comma-separated topics, break them down and search for each individually.

Create diverse search queries by:
1. Each topic keyword individually (e.g., "Transformers", "Neural Networks")
2. Topic keywords + group keywords (e.g., "Deep Learning AI", "Machine Learning Technology")
3. Combinations of related topics (e.g., "Reinforcement Learning Deep Learning")
4. Technical variations and synonyms

Execute 12-15 different search queries across available tools to ensure comprehensive coverage.

=== OUTPUT REQUIREMENTS ===

After collecting search results, analyze and extract the most relevant and recent news items. For each news item, provide:

- title: A concise title (max 15 words)
- summary: A comprehensive summary (At least 1-2 paragraphs, 150-250 words)
- sources: List of Source URLs from the search results - each URL must be valid
- topic: {current_topic}
- groups: {current_groups}
- published_date: The publication date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Extract from search results if available.
- tool_source: The tool that provided this news item (must be one of: "arxiv", "tavily", "wikipedia", or "reddit")

IMPORTANT: For tool_source, specify which tool you used to find each news item:
- If from ArXiv search results → tool_source: "arxiv"
- If from Tavily search results → tool_source: "tavily"
- If from Wikipedia search results → tool_source: "wikipedia"
- If from Reddit search results → tool_source: "reddit"

Focus on unique, high-quality news items and avoid duplicates. Prioritize recent and authoritative sources."""

    user_prompt = """Please collect the latest news for the topic "{current_topic}" related to {current_groups}.

IMPORTANT: You MUST use the specified tools: {preferred_tools}

Search strategy based on available tools:
- If Wikipedia is available: Start with 2-3 queries to understand key concepts and context
- If ArXiv is available: Use 5-10 queries to find recent research papers and developments
- If Tavily is available: Use 5-10 queries to find recent news articles and announcements
- If Reddit is available: Use 3-5 queries across the specified subreddits: {subreddits}
  IMPORTANT: When calling Reddit tool, always include the "subreddit" parameter from the list above

Make 12-15 total tool calls using only the tools specified above. Analyze all results and synthesize a comprehensive list of unique news items with proper summaries and source attribution.

Begin searching now."""

    return create_reactive_graph(
        prompt=user_prompt,
        system_prompt=system_prompt,
        output_key="current_news_items",
        tools=tools,
        passthrough_keys=[
            "current_topic",
            "current_groups",
            "days_filter",
            "max_items_per_topic",
            "today_date",
            "is_research_topic",
            "preferred_tools",
            "subreddits",
        ],
        aggregate_output=False,
        max_tool_calls=15,
        extracted_output_key="news_items",
        max_tokens=16000,
        extractor_prompt="""Extract news items from the following input text: {content}""",
    )


def create_main_news_agent():
    """Create the main news agent orchestrator."""

    builder = StateGraph(MainNewsAgentState)

    builder.add_node("load_topics", load_topics_data)
    builder.add_node("route_to_next_topic", route_to_next_topic)
    builder.add_node("process_topic", create_news_worker_agent().compile())
    builder.add_node("deduplicate_collections", deduplicate_collections)
    builder.add_node("save_collections", save_collections)

    builder.set_entry_point("load_topics")
    builder.add_edge("load_topics", "route_to_next_topic")
    builder.add_edge("process_topic", "route_to_next_topic")
    builder.add_edge("deduplicate_collections", "save_collections")
    builder.add_edge("save_collections", END)

    return builder


# Initialize callback handlers
# Langfuse: Tracks everything in cloud dashboard (reads from env vars)
langfuse_handler = CallbackHandler()
# Console logger: Prints tool calls in real-time to terminal
console_logger = ConsoleToolLogger()

graph = (
    create_main_news_agent()
    .compile()
    .with_config(
        config={
            "callbacks": [langfuse_handler, console_logger],
            "checkpointer": MemorySaver(),
            "recursion_limit": 500,
        }
    )
)


async def run_graph():
    initial_state = {"messages": []}
    result = await graph.ainvoke(initial_state)
    logger.info(result)


# Run the asynchronous function
if __name__ == "__main__":
    asyncio.run(run_graph())
