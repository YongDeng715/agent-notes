import os
import yaml
import requests
from langchain.tools import tool

def get_brave_api_key():
    CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf.yaml')
    with open(CONF_PATH, 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
    return conf.get('BRAVE', {}).get('api_key')

@tool
def brave_retriever_tool(query: str) -> list:
    """Search Brave for the given query and return a list of results."""
    api_key = get_brave_api_key()
    if not api_key:
        return ["Brave API key not set in conf.yaml"]
    # The Brave Search API is not public; this is a placeholder for demonstration.
    # Replace with actual Brave API endpoint and logic if available.
    # url = "https://api.brave.com/search"
    # headers = {"Authorization": f"Bearer {api_key}"}
    # params = {"q": query, "num": 5}
    # try:
    #     resp = requests.get(url, headers=headers, params=params, timeout=10)
    #     resp.raise_for_status()
    #     data = resp.json()
    #     return [f"{item.get('title', '')}: {item.get('url', '')}" for item in data.get('results', [])]
    # except Exception as e:
    #     return [f"Brave search error: {e}"]
    # Mocked response:
    return [f"Brave search result for '{query}' (mocked)"] 