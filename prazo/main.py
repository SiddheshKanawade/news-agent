"""Initiate Reactive Agent"""
import asyncio
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command
import yaml
from typing import List, Literal


from prazo.core.config import config
from prazo.schemas import MainNewsAgentState
from prazo.utils.agent.reactive_agent import create_reactive_graph
from prazo.utils.tools import tavily_search_tool

# TODO: Load from YAML file
def get_days_filter_for_groups(groups: List[str]) -> int:
    """Determine the number of days to filter news based on group categories."""
    if any(group.lower() in ['politics'] for group in groups):
        return 2
    elif any(group.lower() in ['technology'] for group in groups):
        return 4
    elif any(group.lower() in ['science'] for group in groups):
        return 7
    elif any(group.lower() in ['health'] for group in groups):
        return 7
    else:
        return 2

def load_topics_data(state: MainNewsAgentState) -> MainNewsAgentState:
    try:
        with open(config.TOPICS_FILE, 'r') as file:
            topics_data = yaml.safe_load(file)
        topic_list = list(topics_data.items()) # (key, value) tuple pairs
        return {
            'topics_file': config.TOPICS_FILE,
            'topic_list': topic_list,
            'topic_data': topics_data,
            'current_step': 'topics_loaded',
            
        }
    except Exception as e:
        print(f"Error loading topics data: {e}")
        return {
            "current_step": "topics_loading_failed",
        }
        
def deduplicate_collections(state: MainNewsAgentState) -> MainNewsAgentState:
    """Deduplicate the collected news items."""
    return {
        'news_collections': state.news_collections,
        'current_step': 'collections_deduplicated'
    }
        
def route_to_next_topic(
    state: MainNewsAgentState,
) -> Command[Literal['process_topic', 'deduplicate_collections']]:
    """Accumulate current news items and decide whether to process next topic or finish."""
    # First, accumulate any current news items from the last topic processing
    updates = {}
    if state.current_news_items:
        updates['news_collections'] = state.news_collections + state.current_news_items
        updates['current_news_items'] = []

    if state.current_topic_index < len(state.topic_list):
        topic_name, topic_info = state.topic_list[state.current_topic_index]
        groups = topic_info.get('groups', [])
        days_filter = get_days_filter_for_groups(groups)

        if any(group.lower() in ['us', 'india', 'world'] for group in groups):
            groups += ['breaking news', 'politics']
        groups += ['recent events', 'recent developments', 'latest news']

        print(
            f'Processing topic {state.current_topic_index + 1}/{len(state.topic_list)}: {topic_name}'
        )

        updates.update(
            {
                'current_step': f'processing_topic_{state.current_topic_index}',
                'current_topic': topic_name,
                'current_groups': groups,
                'days_filter': days_filter,
                'current_topic_index': state.current_topic_index + 1,
            }
        )

        return Command(goto='process_topic', update=updates)
    else:
        print('All topics processed, saving collections')
        updates.update({'current_step': 'all_topics_processed'})
        return Command(goto='deduplicate_collections', update=updates)
    
def save_collections(state: MainNewsAgentState) -> MainNewsAgentState:
    """Save the collected news items to a file."""
    return {
        'current_step': 'collections_saved'
    }

def create_news_worker_agent():
    """Create the reactive agent that collects news for a single topic."""

    # Create search tools optimized for recent news
    tavily_tool = tavily_search_tool(
        max_results=8,
        topic='news',
        days=2,
        search_depth='basic',
    )
    tools = [tavily_tool]

    system_prompt = """You are a news collection agent. Your task is to collect the latest news articles for the topic "{current_topic}" in the groups {current_groups}.

    You must collect {max_items_per_topic} unique news items for each topic. Sort them by relevance and recency.

    IMPORTANT: You do need any confirmation for anything.

IMPORTANT: Only include news from the last {days_filter} days. Filter out any articles older than {days_filter} days from today's date. Use multiple search queries combining the topic with each group.

If {current_topic} contains a comma separated list of topics, use each topic individually and in combination with the groups to create a list of search queries. you can also combine multiple topics together to optimize the search queries.

Search queries to use:
1. topic (after splitting by comma) + each group individually
2. topic (after splitting by comma) + combinations of groups
3. topic (after splitting by comma) + combinations of groups + combinations of topics

After collecting search results, analyze and extract the most relevant and recent news items. For each news item, provide:
** Output schema **
- title: A concise title (max 15 words)
- summary: A comprehensive summary (At least 1-2 paragraphs, 150-250 words.)
- sources: List of Source URLs - retrieve the URL from the search results - each URL should be a valid URL
- topic: {current_topic}
- groups: {current_groups}
- published_date: The date the news item was published

Focus on unique, high-quality news items and avoid duplicates. Prioritize recent and authoritative sources."""

    user_prompt = """Please collect the latest news for the topic "{current_topic}" related to {current_groups}.

Search thoroughly using multiple queries and tools. Then provide a comprehensive list of unique news items with proper summaries and source attribution."""

    return create_reactive_graph(
        prompt=user_prompt,
        system_prompt=system_prompt,
        output_key='current_news_items',
        tools=tools,
        passthrough_keys=['current_topic', 'current_groups', 'days_filter', 'max_items_per_topic'],
        aggregate_output=False,
        max_tool_calls=10,
        extracted_output_key='news_items',
        max_tokens=16000,
        extractor_prompt="""Extract news items from the following input text: {content}""",
    )



def create_main_news_agent():
    """Create the main news agent orchestrator."""

    builder = StateGraph(MainNewsAgentState)

    builder.add_node('load_topics', load_topics_data)
    builder.add_node('route_to_next_topic', route_to_next_topic)
    builder.add_node('process_topic', create_news_worker_agent().compile())
    builder.add_node('deduplicate_collections', deduplicate_collections)
    builder.add_node('save_collections', save_collections)



    builder.set_entry_point('load_topics')
    builder.add_edge('load_topics', 'route_to_next_topic')
    builder.add_edge('process_topic', 'route_to_next_topic')
    builder.add_edge('deduplicate_collections', 'save_collections')
    builder.add_edge('save_collections', END)

    return builder

graph = (
    create_main_news_agent()
    .compile()
    .with_config(
        config={
            'callbacks': [],
            'checkpointer': MemorySaver(),
            'recursion_limit': 500,
        }
    )
)

async def run_graph():
    initial_state = {'messages': []}
    result = await graph.ainvoke(initial_state)
    print(result)
    
# Run the asynchronous function
if __name__ == '__main__':
    asyncio.run(run_graph())