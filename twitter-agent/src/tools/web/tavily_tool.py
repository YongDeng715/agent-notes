import os
import yaml
import requests
from langchain.tools import tool

def get_tavily_api_key():
    CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf.yaml')
    with open(CONF_PATH, 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
    return conf.get('TAVILY', {}).get('api_key')

@tool
def tavily_retriever_tool(query: str) -> list:
    """Search Tavily for the given query and return a list of results."""
    api_key = get_tavily_api_key()
    if not api_key:
        return ["Tavily API key not set in conf.yaml"]
    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "query": query,
        "max_results": 5,
        "search_depth": "basic",
        "topic": "general",
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
        "include_image_descriptions": False,
        "include_domains": [],
        "exclude_domains": []
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Assume data['results'] is a list of dicts with 'title' and 'url'
        return [f"{item.get('title', '')}: {item.get('url', '')}" for item in data.get('results', [])]
    except Exception as e:
        return [f"Tavily search error: {e}"]