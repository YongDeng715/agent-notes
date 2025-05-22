import os
import yaml
from langchain.tools import tool
from .tavily_tool import tavily_retriever_tool
from .duckduckgo_tool import duckduckgo_retriever_tool
from .arxiv_tool import arxiv_retriever_tool
from .brave_tool import brave_retriever_tool
from collections import OrderedDict

def get_search_api_names():
    CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf.yaml')
    with open(CONF_PATH, 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
    # Support both old 'name' and new 'names' config for backward compatibility
    names = conf.get('SEARCH_API', {}).get('names')
    if names is None:
        name = conf.get('SEARCH_API', {}).get('name', 'tavily')
        return [name.lower()]
    return [n.lower() for n in names]

TOOL_MAP = {
    'tavily': tavily_retriever_tool,
    'duckduckgo': duckduckgo_retriever_tool,
    'arxiv': arxiv_retriever_tool,
    'brave': brave_retriever_tool,
}

@tool
def search_tool(query: str) -> list:
    """Aggregated search tool. Calls all configured engines and merges results."""
    api_names = get_search_api_names()
    all_results = []
    for name in api_names:
        tool_func = TOOL_MAP.get(name)
        if tool_func:
            try:
                results = tool_func.invoke(query)
                if isinstance(results, list):
                    all_results.extend(results)
                else:
                    all_results.append(str(results))
            except Exception as e:
                all_results.append(f"{name} search error: {e}")
        else:
            all_results.append(f"Unknown search tool: {name}")
    # Deduplicate and keep order
    deduped = list(OrderedDict.fromkeys([r for r in all_results if r and isinstance(r, str)]))
    # Optionally: sort or rank results here
    return deduped[:10]  # Return top 10 merged results

search_tools = [search_tool]

from llm_loader import get_chat_openai
# Import necessary message types
from langchain_core.messages import HumanMessage, SystemMessage

if __name__ == "__main__":
    # Test the search tool via LLM
    print("Testing search tool via LLM...")
    llm = get_chat_openai(temperature=0) # Ensure your conf.yaml BASIC_MODEL is set up correctly
    llm_with_tools = llm.bind_tools(search_tools)

    # test_query = "国内大厂关于AI-Agent的最新成果"
    test_query = "Search for papers about VLM Agent"
    # Add a SystemMessage to guide the LLM
    messages = [
        SystemMessage(content="You are a helpful assistant that can use tools to find information."),
        HumanMessage(content=test_query)
    ]

    print(f"Invoking LLM with query: {test_query}")
    response = llm_with_tools.invoke(messages)

    print("LLM Response:")
    print(response)

    if response.tool_calls:
        print("LLM called a tool. Executing tool call...")
        tool_call = response.tool_calls[0]
        # Accessing tool call details depends on the model's output format,
        # LangChain standardizes this in .tool_calls on the AIMessage.
        tool_name = tool_call.get('name') # Use .get for safety
        tool_args = tool_call.get('args') # Use .get for safety

        if tool_name == "search_tool":
            print(f"Calling {tool_name} with args: {tool_args}")
            try:
                # LangChain tools can be invoked directly by name from the list
                # Find the tool by name
                # Ensure the tool object has a .name attribute
                selected_tool = next((item for item in search_tools if hasattr(item, 'name') and item.name == tool_name), None)
                if selected_tool:
                    # Ensure tool_args is a dictionary if the tool expects kwargs
                    tool_result = selected_tool.invoke(tool_args)
                    print("Tool Result:")
                    print(tool_result)
                else:
                    print(f"Error: Tool {tool_name} not found or has no name attribute.")
            except Exception as e:
                print(f"Error executing tool {tool_name}: {e}")
        else:
            print(f"LLM called an unexpected tool: {tool_name}")
    else:
        print("LLM did not call a tool.")