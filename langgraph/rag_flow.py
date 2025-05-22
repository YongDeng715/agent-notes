from typing import Annotated
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition

from nodes import grade_documents, rewrite, generate
from agent import AgentState, agent
from web.search_tool import search_tools


def build_graph():
    workflow = StateGraph(AgentState)

    # Define the nodes we will cycle between
    workflow.add_node("agent", agent)  # agent
    retrieve = ToolNode(search_tools)
    workflow.add_node("retrieve", retrieve)  # retrieval
    workflow.add_node("rewrite", rewrite)  # Re-writing the question
    workflow.add_node(
        "generate", generate
    )  # Generating a response after we know the documents are relevant
    # Call agent node to decide to retrieve or not
    workflow.add_edge(START, "agent")

    # Decide whether to retrieve
    workflow.add_conditional_edges(
        "agent",
        # Assess agent decision
        tools_condition,
        {
            # Translate the condition outputs to nodes in our graph
            "tools": "retrieve",
            END: END,
        },
    )
    # Edges taken after the `action` node is called.
    workflow.add_conditional_edges(
        "retrieve",
        # Assess agent decision
        grade_documents,
    )
    workflow.add_edge("generate", END)
    workflow.add_edge("rewrite", "agent")
    
    graph = workflow.compile()  # Compile
    return graph

from IPython.display import Image, display
import pprint

if __name__ == "__main__":
    graph = build_graph()

    try:
        # 生成图的流程图片，写到目录
        qa_async_png = graph.get_graph(xray=True).draw_mermaid_png()
        display(Image(qa_async_png))
        with open("../assets/langgraph/rag_agent_flow.png", "wb") as f:
            f.write(qa_async_png)
    except Exception as e:
        # This requires some extra dependencies and is optional
        print(f"Failed to generate graph image: {e}")
        pass

    user_input = "搜索国内外大厂关于Agent的最新研究成果，撰写一份有质量的X推文介绍"
    inputs = {
        "messages": [
            ("user", f"{user_input}"),
        ]
    }

    all_contents = []
    for output in graph.stream(inputs):
        for key, value in output.items():
            pprint.pprint("-"*10 + f"Output from node '{key}':" + "-"*10)
            pprint.pprint(value, indent=2, width=80, depth=None)
            all_contents.append(value)
        print("\n"+"----"*10+"\n")
    
    # 打印最终所有输出内容
    if all_contents:
        last_content = all_contents[-1]["messages"][0].content
        print("\n===== 总输出内容（最后一次迭代的 output） =====\n")
        pprint.pprint(last_content, indent=2, width=80, depth=None, compact=False)
    else:
        print("\n===== 没有输出 =====\n")