from langgraph.graph import MessageState, StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from planner import Plan

from .nodes import (
    coordinator_node,
    planner_node,
    reporter_node,
    researcher_node,
    drawer_node,
    poster_node
)


class State(MessageState):
    """State for the agent system, extends MessagesState with next field."""

    # Runtime Variables
    plan_iterations: int = 0
    current_plan: Plan | str = None
    final_report: str = None


def _build_basic_graph():
    """Build and return the base state graph with all nodes and edges."""
    builder = StateGraph(State)

    builder.add_node('coordinator', coordinator_node)
    builder.add_node('planner', planner_node)
    builder.add_node('reporter', reporter_node)
    builder.add_node('researcher', researcher_node)
    builder.add_node('drawer', drawer_node)

    builder.add_edge(START, 'coordinator')
    builder.add_edge('reported', END)
    return builder

def build_graph_with_memory():
    """Build and return the agent workflow graph with memory."""
    # use persistent memory to save conversation history
    # TODO: be compatible with SQLite / PostgreSQL
    memory = MemorySaver()

    # build state graph
    builder = _build_basic_graph()
    return builder.compile(checkpointer=memory)


def build_graph():
    """Build and return the agent workflow graph without memory."""
    # build state graph
    builder = _build_basic_graph()
    return builder.compile()


##### 
if __name__ == '__main__':
    graph = build_graph()

    from IPython.display import Image, display
    try:
        # 生成图的流程图片，写到目录
        qa_async_png = graph.get_graph(xray=True).draw_mermaid_png()
        display(Image(qa_async_png))
        with open("x_agent_flow.png", "wb") as f:
            f.write(qa_async_png)
    except Exception:
        # This requires some extra dependencies and is optional
        pass

    import pprint
    inputs = {
        "messages": [
            ("user", "What does Lilian Weng say about the types of agent memory?"),
        ]
    }
    for output in graph.stream(inputs):
        for key, value in output.items():
            pprint.pprint(f"Output from node '{key}':")
            pprint.pprint("---")
            pprint.pprint(value, indent=2, width=80, depth=None)
        pprint.pprint("\n---\n")