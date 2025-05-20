from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
# from planner import Plan  # Not used, remove for now

from .nodes import (
    planner_node,
    research_team,
    poster_node,
    State
)

# Twitter workflow: planner -> research_team -> poster

def _build_basic_graph():
    """Build and return the base state graph with all nodes and edges."""
    builder = StateGraph(State)

    builder.add_node('planner', planner_node)
    builder.add_node('research_team', research_team)
    builder.add_node('poster', poster_node)
    builder.add_edge(START, 'planner')
    builder.add_edge('planner', 'research_team')
    builder.add_edge('research_team', 'poster')
    builder.add_edge('poster', END)
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
    except Exception as e:
        # This requires some extra dependencies and is optional
        print(f"Failed to generate graph image: {e}")
        pass
    
    import pprint
    inputs = {
        "messages": [
            ("user", "Post a tweet: Hello Twitter! This is a test tweet from LangGraph agent."),
        ]
    }
    for output in graph.stream(inputs):
        for key, value in output.items():
            pprint.pprint("-"*10 + f"Output from node '{key}':" + "-"*10)
            pprint.pprint(value, indent=2, width=80, depth=None)
        print("\n#####----------#####\n")