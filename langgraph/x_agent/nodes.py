import random
from langgraph.types import Command, interrupt
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState
from dataclasses import dataclass, field
from typing import List, Dict, Any

from .agent import create_agent
from .configuration import Configuration, AGENT_LLM_MAP
from .llm import get_llm_by_type
from .search_tools import web_search_tool
from .x_tools import x_post_tool

# --- Plan structure ---
@dataclass
class SubTask:
    id: str
    type: str  # 'research' or 'draw'
    description: str
    params: dict = field(default_factory=dict)

@dataclass
class Plan:
    tweet_text: str
    subtasks: List[SubTask]

class State(MessagesState):
    """State for the agent system, extends MessagesState with next field."""

    # Runtime Variables
    plan_iterations: int = 0
    current_plan: dict | str = None
    final_report: str = None
    tweet_id: str = None

# --- Node: Planner ---
def extract_user_message(msg):
    # 兼容 tuple, dict, HumanMessage, str
    if isinstance(msg, str):
        return msg
    elif isinstance(msg, tuple):
        return msg[1]
    elif hasattr(msg, "content"):
        return msg.content
    elif isinstance(msg, dict) and "content" in msg:
        return msg["content"]
    else:
        return str(msg)

def planner_node(state: State, config: RunnableConfig = None):
    """Use LLM to generate a plan with multiple subtasks for researcher and drawer."""
    user_message = extract_user_message(state["messages"][-1]) if state["messages"] else ""
    print(f"User message: {user_message}\n")
    print("Planner generating full plan.")

    configurable = Configuration.from_runnable_config(config)
    plan_iterations = state["plan_iterations"] if state.get("plan_iterations", 0) else 0
    messages = [{
        "role": "user",
        "content": user_message
    }]
    
    if (
        plan_iterations == 0
        and state.get("enable_background_invastigation")
        and state.get("background_invastigation_results")
    ):
        messages += [
            {
                "role": "user",
                "content": (
                    "background investigation results of user query:\n"
                    + state["background_invastigation_results"] + "\n"
                )
            }
        ]
        
    # Compose prompt for LLM
    prompt = f"""
    You are a planner agent for a Twitter posting workflow. Given the user request below, break it down into a tweet_text and a list of subtasks. Each subtask should be either a research or draw task, with a unique id, type, description, and any needed params.
    User request: {user_message}
    Output JSON with keys: tweet_text, subtasks (list of dicts with id, type, description, params).
    """
    llm = get_llm_by_type(AGENT_LLM_MAP["planner"])
    plan_json = llm.invoke(prompt)
    # For demo, fallback if LLM output is not structured
    try:
        import json
        plan_data = json.loads(plan_json)
        subtasks = [SubTask(**st) for st in plan_data.get("subtasks", [])]
        plan = Plan(tweet_text=plan_data.get("tweet_text", ""), subtasks=subtasks)
    except Exception:
        # Fallback: simple plan
        plan = Plan(
            tweet_text=f"[Planned Tweet] {user_message}",
            subtasks=[
                SubTask(id="r1", type="research", description=f"Background for: {user_message}"),
                SubTask(id="d1", type="draw", description=f"Illustration for: {user_message}")
            ]
        )
    # Store subtasks in state for research_team_node
    state["current_plan"] = plan
    state["subtasks"] = plan.subtasks
    state["research_results"] = []
    state["draw_results"] = []
    return state

# --- Node: Researcher ---
def researcher_node(subtasks: List[SubTask]):
    results = []
    for task in subtasks:
        result = {"id": task.id, "result": f"[Research result for] {task.description}"}
        results.append(result)
    return results

# --- Node: Drawer ---
def drawer_node(subtasks: List[SubTask]):
    results = []
    for task in subtasks:
        result = {"id": task.id, "image_url": f"http://fakeimg.com/{task.id}"}
        results.append(result)
    return results

# --- Node: Research Team (dispatches subtasks) ---
def research_team(state: State, config: RunnableConfig = None):
    """Dispatch subtasks to researcher_node and drawer_node, collect results."""
    subtasks = state.get("subtasks", [])
    research_subtasks = [st for st in subtasks if st.type == "research"]
    draw_subtasks = [st for st in subtasks if st.type == "draw"]
    research_results = researcher_node(research_subtasks) if research_subtasks else []
    draw_results = drawer_node(draw_subtasks) if draw_subtasks else []
    state["research_results"] = research_results
    state["draw_results"] = draw_results
    return state

# --- Node: Poster ---
def poster_node(state: State, config: RunnableConfig = None):
    """Assemble all results and post the tweet with text and image (if any)."""
    plan = state.get("current_plan", None)
    tweet_text = plan.tweet_text if plan else "Test tweet from LangGraph agent."
    research_results = state.get("research_results", [])
    draw_results = state.get("draw_results", [])
    # Compose tweet content
    research_summary = "\n".join([r["result"] for r in research_results])
    image_url = draw_results[0]["image_url"] if draw_results else None
    full_text = tweet_text + "\n" + research_summary
    # For demo, just append image url to text
    if image_url:
        full_text += f"\n[Image: {image_url}]"
    tweet_id = x_post_tool(full_text)
    state["tweet_id"] = tweet_id
    state["final_report"] = f"Tweet posted with ID: {tweet_id}"
    return state


