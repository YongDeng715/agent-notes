import os
import yaml
import requests
from langchain.tools import tool
from xml.etree import ElementTree

def get_arxiv_api_key():
    CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf.yaml')
    with open(CONF_PATH, 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
    return conf.get('ARXIV', {}).get('api_key')

@tool
def arxiv_retriever_tool(query: str) -> list:
    """Search Arxiv for the given query and return a list of results (title: url)."""
    url = "http://export.arxiv.org/api/query"
    params = {"search_query": query, "start": 0, "max_results": 5}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        results = []
        for entry in root.findall('atom:entry', ns):
            title_elem = entry.find('atom:title', ns)
            link_elem = entry.find('atom:id', ns)
            title = title_elem.text.strip() if title_elem is not None else "No Title"
            link = link_elem.text.strip() if link_elem is not None else ""
            if link:
                results.append(f"{title}: {link}")
        return results or ["Arxiv: No relevant results found."]
    except Exception as e:
        return [f"Arxiv search error: {e}"] 