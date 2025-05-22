import os
import yaml
import requests
from langchain.tools import tool

def get_duckduckgo_api_key():
    CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf.yaml')
    with open(CONF_PATH, 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
    return conf.get('DUCKDUCKGO', {}).get('api_key')

@tool
def duckduckgo_retriever_tool(query: str) -> list:
    """Search DuckDuckGo for the given query and return a list of results."""
    # DuckDuckGo Instant Answer API does not require an API key
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        if 'RelatedTopics' in data:
            for item in data['RelatedTopics']:
                if 'Text' in item and 'FirstURL' in item:
                    results.append(f"{item['Text']}: {item['FirstURL']}")
        if not results and 'AbstractText' in data and data['AbstractText']:
            results.append(data['AbstractText'])
        return results or ["No results found."]
    except Exception as e:
        return [f"DuckDuckGo search error: {e}"] 