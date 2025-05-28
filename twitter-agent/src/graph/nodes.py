import os
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command, interrupt
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState
from dataclasses import dataclass, field
from typing import List, Annotated, Literal

from .agent import create_agent
from .configuration import Configuration, AGENT_LLM_MAP
from .llm import get_llm_by_type
from src.tools.search_tool import web_search_tool, crawl_tool
from src.tools.x_tool import x_post_tool, mock_draw_tool

# --- Plan structure ---
@dataclass
class SubTask:
    id: int
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

PLAN_SYSTEM_PROMPT = """
You are a X(formerly Twitter) planning agent. Your task is to create a actionable plan 
composed of many clear subtasks to post tweets based on the user's post request.

Firstly you need to think about the 'maintask' of the user's request, then list a series of
interdependent key subtasks to execute.

provide your response in JSON format with the following structure as an example:
{
    'maintask': 'Plan steps to post the user's first tweet',
    'subtasks': [
        {'research':'Draft the basic content about the user's infomation based on the user's request'},
        {'research':'Generate a list of images about the user's hobbies, accomplishments, etc.'},
        {'draw':'Add some content about the user's hobbies, accomplishments, etc.'},
        {'research':'Composed the above content into a tweet text'},
    ]
}
"""

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
    except Exception as e:
        print(f"LLM output is not structured: {plan_json}")
        print(f"Error: {e}")
        plan = None
        """# Fallback: simple plan
        plan = Plan(
            tweet_text=f"[Planned Tweet] {user_message}",
            # description=f"Complete descrtiption and appropriate supplementations for user's request."
            subtasks=[
                SubTask(id="r1", type="research", description=f"Background for: {user_message}"),
                SubTask(id="d1", type="draw", description=f"Illustration for: {user_message}")
            ]
        )
        """
    
    # Store subtasks in state for research_team_node
    state["current_plan"] = plan
    state["subtasks"] = plan.subtasks
    state["research_results"] = []
    state["draw_results"] = []
    return state

# --- Node: Researcher ---
# 明确 default_tools 和 agent_type
default_tools = [web_search_tool, crawl_tool]
agent_type = "researcher"

import asyncio

async def researcher_node(state: State, config: RunnableConfig = None):
    """遍历 research 类型的 subtasks，依次执行并收集结果，存入 state['research_results']，并返回 state。"""
    print("Researcher node is researching.")
    configurable = Configuration.from_runnable_config(config)
    research_subtasks = [st for st in state.get("subtasks", []) if st.type == "research"]
    results = []
    for subtask in research_subtasks:
        # 构造 agent 并执行
        agent = create_agent(agent_type, agent_type, default_tools, agent_type)
        # 构造输入
        agent_input = {
            "messages": [
                HumanMessage(content=f"# Task\n\n## Title\n\n{subtask.description}\n\n## Params\n{subtask.params}")
            ]
        }
        # 执行 agent
        result = await agent.ainvoke(input=agent_input)
        content = result["messages"][-1].content if "messages" in result and result["messages"] else str(result)
        results.append({"id": subtask.id, "result": content})
    state["research_results"] = results
    return state

# --- Node: Drawer ---
def drawer_node(subtasks: List[SubTask]):
    results = []
    for task in subtasks:
        # 调用模拟图片生成接口
        image_url = mock_draw_tool(task.description, task.params)
        result = {"id": task.id, "image_url": image_url}
        results.append(result)
    return results

    

# --- Node: Research Team (dispatches subtasks) ---
async def research_team(state: State, config: RunnableConfig = None):
    """异步调度 researcher_node 和 drawer_node，收集结果。"""
    subtasks = state.get("subtasks", [])
    research_subtasks = [st for st in subtasks if st.type == "research"]
    draw_subtasks = [st for st in subtasks if st.type == "draw"]
    # 异步执行 research
    if research_subtasks:
        state = await researcher_node(state, config)
    # 同步执行 draw
    draw_results = drawer_node(draw_subtasks) if draw_subtasks else []
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

async def _execute_agent_step(
    state: State, agent, agent_name: str
) -> Command[Literal["research_team"]]:
    """Helper function to execute a step using the specified agent."""
    current_plan = state.get("current_plan")
    observations = state.get("observations", [])

    # Find the first unexecuted step
    current_step = None
    completed_steps = []
    for step in current_plan.steps:
        if not step.execution_res:
            current_step = step
            break
        else:
            completed_steps.append(step)

    if not current_step:
        print("No unexecuted step found")
        return Command(goto="research_team")

    print(f"Executing step: {current_step.title}")

    # Format completed steps information
    completed_steps_info = ""
    if completed_steps:
        completed_steps_info = "# Existing Research Findings\n\n"
        for i, step in enumerate(completed_steps):
            completed_steps_info += f"## Existing Finding {i+1}: {step.title}\n\n"
            completed_steps_info += f"<finding>\n{step.execution_res}\n</finding>\n\n"

    # Prepare the input for the agent with completed steps info
    agent_input = {
        "messages": [
            HumanMessage(
                content=f"{completed_steps_info}# Current Task\n\n## Title\n\n{current_step.title}\n\n## Description\n\n{current_step.description}\n\n## Locale\n\n{state.get('locale', 'en-US')}"
            )
        ]
    }

    # Add citation reminder for researcher agent
    if agent_name == "researcher":
        agent_input["messages"].append(
            HumanMessage(
                content="IMPORTANT: DO NOT include inline citations in the text. Instead, track all sources and include a References section at the end using link reference format. Include an empty line between each citation for better readability. Use this format for each reference:\n- [Source Title](URL)\n\n- [Another Source](URL)",
                name="system",
            )
        )

    # Invoke the agent
    default_recursion_limit = 25
    try:
        env_value_str = os.getenv("AGENT_RECURSION_LIMIT", str(default_recursion_limit))
        parsed_limit = int(env_value_str)

        if parsed_limit > 0:
            recursion_limit = parsed_limit
            logger.info(f"Recursion limit set to: {recursion_limit}")
        else:
            logger.warning(
                f"AGENT_RECURSION_LIMIT value '{env_value_str}' (parsed as {parsed_limit}) is not positive. "
                f"Using default value {default_recursion_limit}."
            )
            recursion_limit = default_recursion_limit
    except ValueError:
        raw_env_value = os.getenv("AGENT_RECURSION_LIMIT")
        logger.warning(
            f"Invalid AGENT_RECURSION_LIMIT value: '{raw_env_value}'. "
            f"Using default value {default_recursion_limit}."
        )
        recursion_limit = default_recursion_limit

    result = await agent.ainvoke(
        input=agent_input, config={"recursion_limit": recursion_limit}
    )

    # Process the result
    response_content = result["messages"][-1].content
    print(f"{agent_name.capitalize()} full response: {response_content}")

    # Update the step with the execution result
    current_step.execution_res = response_content
    logger.info(f"Step '{current_step.title}' execution completed by {agent_name}")

    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response_content,
                    name=agent_name,
                )
            ],
            "observations": observations + [response_content],
        },
        goto="research_team",
    )