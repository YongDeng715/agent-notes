from langgraph.prebuilt import create_react_agent

from prompts import apply_prompt_template
from search_tools import *
from x_tools import *

from llm import get_llm_by_type
from configuration import AGENT_LLM_MAP


# Create agents using configured LLM types
def create_agent(agent_name: str, agent_type: str, tools: list, prompt_template: str):
    """Factory function to create agents with consistent configuration."""
    return create_react_agent(
        name=agent_name,
        model=get_llm_by_type(AGENT_LLM_MAP[agent_type]),
        tools=tools,
        prompt=lambda state: apply_prompt_template(prompt_template, state),
    )


# Create agents using the factory function
research_agent = create_agent(
    "researcher", "researcher", [web_search_tool, crawl_tool], "researcher"
)
coder_agent = create_agent("coder", "coder", [python_repl_tool], "coder")