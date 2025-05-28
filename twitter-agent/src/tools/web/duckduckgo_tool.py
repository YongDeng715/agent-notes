import os
import yaml
from langchain.tools import tool
from duckduckgo_search import DDGS

def get_duckduckgo_api_key():
    CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf.yaml')
    with open(CONF_PATH, 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
    return conf.get('DUCKDUCKGO', {}).get('api_key')

@tool
def duckduckgo_retriever_tool(query: str) -> list:
    """Search DuckDuckGo for the given query and return a list of results."""
    try:
        # Use DDGS for robust search, region set to 'cn-zh' for Chinese
        results = DDGS().text(query, region="cn-zh", safesearch="off", max_results=10)
        output = []
        for item in results:
            title = item.get('title')
            url = item.get('href')
            if title and url:
                output.append(f"{title}: {url}")
        return output or ["DuckDuckGo: No relevant results found."]
    except Exception as e:
        return [f"DuckDuckGo search error: {e}"] 