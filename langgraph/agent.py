import os
import yaml
from typing import Annotated, Sequence
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from web.search_tool import search_tools

class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    messages: Annotated[Sequence[BaseMessage], add_messages]


def get_basic_model_config():
    CONF_PATH = os.path.join(os.path.dirname(__file__), 'conf.yaml')
    if not os.path.exists(CONF_PATH):
        CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf.yaml')
    with open(CONF_PATH, 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
    basic = conf.get('BASIC_MODEL', {})
    return {
        'base_url': basic.get('base_url'),
        'model_name': basic.get('model'),
        'api_key': basic.get('api_key'),
    }

def agent(state):
    """
    Invokes the agent model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply end.

    Args:
        state (messages): The current state

    Returns:
        dict: The updated state with the agent response appended to messages
    """
    print("---CALL AGENT---")
    messages = state["messages"]
    model_conf = get_basic_model_config()
    model = ChatOpenAI(
        base_url=model_conf['base_url'],
        api_key=model_conf['api_key'],
        model_name=model_conf['model_name'],
        temperature=0,
        streaming=False
    )
    model = model.bind_tools(search_tools)
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}