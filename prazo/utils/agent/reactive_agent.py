"""
Reactive Worker Agent

- State - MainNewsAgentState
"""

# Input from parent agent:
# - Topic
# - Groups
# - Tools
# - Max tool calls

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel
from typing import Any, Literal, Optional, List, Dict, Union
from trustcall import create_extractor

from prazo.utils.chat_models import ChatModel
from prazo.schemas import MainNewsAgentState, NewsCollectionOutput

def tools_condition(
    state: Union[list[AnyMessage], dict[str, Any], BaseModel],
    messages_key: str = 'messages',
    max_tool_calls: int = 3,
) -> Literal['tools', 'output_node']:
    if isinstance(state, list):
        ai_message = state[-1]
        messages = state
    elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
        ai_message = messages[-1]
    elif messages := getattr(state, messages_key, []):
        ai_message = messages[-1]
    else:
        raise ValueError(f'No messages found in input state to tool_edge: {state}')
    if hasattr(ai_message, 'tool_calls') and len(ai_message.tool_calls) > 0:
        return 'tools'
    return 'output_node'

def build_prompt(state: MainNewsAgentState, passthrough_keys: List[str], system_prompt: str, prompt: str):
    # Build a dict of values to format the system prompt with
    format_values = {}
    for key in passthrough_keys:
        output_key = input_key = key
        base_val = getattr(state, input_key)
        format_values[output_key] = base_val

    return {
        'messages': [
            SystemMessage(content=system_prompt.format(**format_values)),
            HumanMessage(content=prompt.format(**format_values)),
        ],
        'tool_call_count': 0,
    }

async def assistant(state: MainNewsAgentState, max_tool_calls: int, llm, llm_with_tools) -> MainNewsAgentState:
    tool_call_count = getattr(state, 'tool_call_count', 0)

    # If we've reached max tool calls, use LLM without tools to force final response
    if tool_call_count >= max_tool_calls:
        # Add instruction to provide final response based on gathered information
        messages = state.messages + [
            HumanMessage(
                content="You have gathered enough information. Please provide your final response based on all the information you've collected so far. Do not attempt to use any tools."
            )
        ]
        return {'messages': [await llm.ainvoke(messages)]}
    else:
        return {'messages': [await llm_with_tools.ainvoke(state.messages)]}

def manage_tool_context(state: MainNewsAgentState) -> MainNewsAgentState:
    """Manage tool call context by keeping only the last 2 tool call results and incrementing counter - reduce token usage"""
    messages = state.messages
    tool_call_count = getattr(state, 'tool_call_count', 0) + 1

    # Keep system and human messages (non-tool related)
    preserved_messages = []
    ai_tool_pairs = []  # [(ai_message, [tool_messages])]

    current_ai_msg = None
    current_tool_msgs = []

    for msg in messages:
        if isinstance(msg, (SystemMessage, HumanMessage)):
            preserved_messages.append(msg)
        elif isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            # If we have a pending AI message, save the pair
            if current_ai_msg is not None:
                ai_tool_pairs.append((current_ai_msg, current_tool_msgs))

            # Start new AI message
            current_ai_msg = msg
            current_tool_msgs = []
        elif isinstance(msg, ToolMessage):
            # Add to current tool messages if we have an AI message
            if current_ai_msg is not None:
                current_tool_msgs.append(msg)
        elif isinstance(msg, AIMessage):
            # Regular AI message without tool calls
            # If we have a pending AI message, save the pair first
            if current_ai_msg is not None:
                ai_tool_pairs.append((current_ai_msg, current_tool_msgs))
                current_ai_msg = None
                current_tool_msgs = []

            # This regular AI message should be preserved
            preserved_messages.append(msg)

    # Don't forget the last AI message if it exists
    if current_ai_msg is not None:
        ai_tool_pairs.append((current_ai_msg, current_tool_msgs))

    # Keep only the last 2 AI-tool pairs
    if len(ai_tool_pairs) > 2:
        ai_tool_pairs = ai_tool_pairs[-2:]

    # Reconstruct messages: preserved messages first, then AI-tool pairs in order
    new_messages = preserved_messages.copy()

    for ai_msg, tool_msgs in ai_tool_pairs:
        new_messages.append(ai_msg)
        new_messages.extend(tool_msgs)

    return {
        'messages': new_messages,
        'tool_call_count': tool_call_count,
    }

async def structured_output(state: MainNewsAgentState, llm: BaseChatModel, extractor_prompt: str, aggregate_output: bool, output_key: str, extracted_output_key: Optional[str] = None) -> MainNewsAgentState:
    last_message = state.messages[-1]
    if isinstance(last_message.content, str):
        content = last_message.content
    elif isinstance(last_message.content, list) and last_message.content:
        # Handle different content formats
        first_content = last_message.content[0]
        if isinstance(first_content, dict):
            content = first_content.get('text', str(first_content))
        else:
            content = str(first_content)
    else:
        content = str(last_message.content)
    extractor = create_extractor(llm, tools=[NewsCollectionOutput], tool_choice='any')
    messages = extractor_prompt.format(content=content)
    res = await extractor.ainvoke(messages)

    if aggregate_output:
        return {
            output_key: [
                res['responses'][0]
                if extracted_output_key is None
                else getattr(res['responses'][0], extracted_output_key)
            ],
            'messages': [RemoveMessage(id=REMOVE_ALL_MESSAGES)],
            'tool_call_count': 0,
        }
    else:
        return {
            output_key: (
                res['responses'][0]
                if extracted_output_key is None
                else getattr(res['responses'][0], extracted_output_key)
            ),
            'messages': [RemoveMessage(id=REMOVE_ALL_MESSAGES)],
            'tool_call_count': 0,
        }


def create_reactive_graph(
    prompt: str,
    system_prompt: str,
    output_key: str,
    tools: list[Any],
    extractor_prompt: str = """
        Extract latex and bibliography components from the following input text:
        {content}

        The two components are separated by a `---BIBLIOGRAPHY---` line.
        """,
    passthrough_keys: list[str] = [],
    aggregate_output: bool = False,
    max_tool_calls: int = 3,
    extracted_output_key: Optional[str] = None,
    max_tokens: Optional[int] = None,
    
):
    # Initialize chat models
    llm = ChatModel(provider="openai", model_name="gpt-4o-mini", max_tokens=max_tokens).llm()
    llm_with_tools = llm.bind_tools(tools)
    
    # Build prompt wrapper
    def _build_prompt_wrapper(state: MainNewsAgentState) -> MainNewsAgentState:
        return build_prompt(state, passthrough_keys, system_prompt, prompt)

    # Build assistant
    async def _build_assistant(state: MainNewsAgentState) -> MainNewsAgentState:
        return await assistant(state, max_tool_calls, llm, llm_with_tools)
    
    # Build tool context manager
    def _build_tool_context_manager(state: MainNewsAgentState) -> MainNewsAgentState:
        return manage_tool_context(state)

    # Build output
    async def _build_output(state: MainNewsAgentState) -> MainNewsAgentState:
        return await structured_output(state, llm, extractor_prompt, aggregate_output, output_key, extracted_output_key)
    
    # Create a custom tools condition with the max_tool_calls parameter
    def _custom_tools_condition(state: MainNewsAgentState) -> Literal['tools', 'output_node']:
        return tools_condition(state, max_tool_calls=max_tool_calls)
    
    # Build Graph
    builder = StateGraph(MainNewsAgentState)
    builder.add_node('prompt_builder', _build_prompt_wrapper)
    builder.add_node('assistant', _build_assistant)
    builder.add_node('tools', ToolNode(tools))
    builder.add_node('manage_tool_context', _build_tool_context_manager)
    builder.add_node('output_node', _build_output)
    
    
    builder.set_entry_point('prompt_builder')
    builder.add_edge('prompt_builder', 'assistant')
    builder.add_conditional_edges('assistant', _custom_tools_condition)
    builder.add_edge('tools', 'manage_tool_context')
    builder.add_edge('manage_tool_context', 'assistant')
    builder.add_edge('output_node', END)
    return builder