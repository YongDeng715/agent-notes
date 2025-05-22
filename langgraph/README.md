# LangGraph RAG-Agent: Modular, Configurable Multi-Tool Retrieval-Augmented Generation

本项目演示了如何基于 [LangGraph](https://github.com/langchain-ai/langgraph) 构建模块化、可配置、支持多检索工具的 RAG-Agent 工作流，灵感来源于 DeerFlow。所有 LLM 和工具配置均集中在 `conf.yaml`，支持 Qwen2.5、Deepseek v3 等大模型，以及 Tavily、DuckDuckGo、Arxiv、Brave 等多种 Web 检索聚合。

---

## 目录结构

- `rag_flow.py`：主流程，定义 RAG-Agent 的 LangGraph 工作流。
- `agent.py`：Agent 节点，负责 LLM 推理与工具调用决策。
- `nodes.py`：包含 `grade_documents`（文档相关性判定）、`rewrite`（问题重写）、`generate`（答案生成）等节点。
- `web/`：各类检索工具实现（Tavily、DuckDuckGo、Arxiv、Brave 等）及聚合器。
- `conf.yaml`：所有 LLM、API Key、检索工具配置。
- `llm_loader.py`：统一加载 LLM 配置。
- `simple_test.ipynb`：LangGraph 基础与 RAG-Agent 流程测试样例。

---

## RAG-Agent 工作流结构与代码讲解

### 1. 工作流结构

RAG-Agent 的核心流程如下：

```
START
  |
  v
agent (LLM决策是否需要检索)
  |-------------------|
  |                   |
  v                   v
retrieve         (无需检索)
  |                   |
  v                   v
grade_documents   END
  |      |
  |      v
  |   rewrite (重写问题后回到 agent)
  v
generate (生成最终答案)
  |
  v
END
```

详见 [`rag_flow.py`](./rag_flow.py)：

```python
workflow.add_node("agent", agent)
workflow.add_node("retrieve", ToolNode(search_tools))
workflow.add_node("rewrite", rewrite)
workflow.add_node("generate", generate)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition, {"tools": "retrieve", END: END})
workflow.add_conditional_edges("retrieve", grade_documents)
workflow.add_edge("generate", END)
workflow.add_edge("rewrite", "agent")
```

### 2. Agent 节点（LLM决策与工具调用）

详见 [`agent.py`](./agent.py)：

- Agent 节点会根据当前对话状态，调用 LLM（如 Qwen2.5、Deepseek v3），并根据模型输出决定是否调用检索工具。
- LLM 和工具均通过 `conf.yaml` 配置，支持灵活切换。

```python
def agent(state):
    model_conf = get_basic_model_config()
    model = ChatOpenAI(
        base_url=model_conf['base_url'],
        api_key=model_conf['api_key'],
        model_name=model_conf['model_name'],
        temperature=0,
        streaming=True
    )
    model = model.bind_tools(search_tools)
    response = model.invoke(state["messages"])
    return {"messages": [response]}
```

### 3. 多检索工具聚合与配置

详见 [`web/search_tool.py`](./web/search_tool.py)：

- 支持在 `conf.yaml` 中配置任意组合的检索工具（如 Tavily、DuckDuckGo、Arxiv、Brave）。
- 工具聚合器会依次调用所有配置的工具，合并去重结果，返回给 Agent。

```yaml
SEARCH_API:
  names: ["tavily", "duckduckgo"]
```

```python
TOOL_MAP = {
    'tavily': tavily_retriever_tool,
    'duckduckgo': duckduckgo_retriever_tool,
    'arxiv': arxiv_retriever_tool,
    'brave': brave_retriever_tool,
}
@tool
def search_tool(query: str) -> list:
    api_names = get_search_api_names()
    all_results = []
    for name in api_names:
        tool_func = TOOL_MAP.get(name)
        if tool_func:
            results = tool_func.invoke(query)
            all_results.extend(results if isinstance(results, list) else [str(results)])
    deduped = list(OrderedDict.fromkeys([r for r in all_results if r and isinstance(r, str)]))
    return deduped[:10]
```

### 4. 检索工具实现示例（Tavily）

详见 [`web/tavily_tool.py`](./web/tavily_tool.py)：

- Tavily 工具已修正为 POST + JSON body，符合官方 API 要求。
- 其他工具（DuckDuckGo、Arxiv、Brave）实现方式类似，均可通过配置灵活启用。

```python
@tool
def tavily_retriever_tool(query: str) -> list:
    api_key = get_tavily_api_key()
    url = "https://api.tavily.com/search"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"query": query, "max_results": 5, ...}
    resp = requests.post(url, headers=headers, json=body, timeout=10)
    data = resp.json()
    return [f"{item.get('title', '')}: {item.get('url', '')}" for item in data.get('results', [])]
```

### 5. 相关性判定与问题重写

详见 [`nodes.py`](./nodes.py)：

- `grade_documents` 节点会调用 LLM 判断检索结果是否相关，输出"yes"或"no"。
- 若不相关，`rewrite` 节点会重写用户问题，再次进入 Agent 决策循环。

---

## 配置说明（conf.yaml）

所有 LLM、API Key、检索工具均在 [`conf.yaml`](./conf.yaml) 配置。例如：

```yaml
BASIC_MODEL:
  base_url: "https://api.siliconflow.cn/v1"
  model: "Qwen/Qwen2.5-72B-Instruct"
  api_key: sk-xxx

SEARCH_API:
  names: ["tavily", "duckduckgo"]

TAVILY:
  api_key: tvly-xxx
DUCKDUCKGO:
  api_key: your-duckduckgo-key
ARXIV:
  api_key: your-arxiv-key
BRAVE:
  api_key: your-brave-key
```

---

## 运行与测试

- 推荐先运行 `simple_test.ipynb` 了解 LangGraph 基础用法与 RAG-Agent 流程。
- 直接运行 `rag_flow.py` 可体验完整 RAG-Agent 工作流，支持流式输出与多轮检索。

---

## 参考与扩展

- [LangGraph 官方文档](https://langgraphcn.org/)
- [DeerFlow 项目设计思想](https://github.com/deerflow/deerflow)
- 可根据实际需求扩展更多检索工具、节点类型或自定义 LLM。

---

如需进一步定制或遇到问题，欢迎提 issue 或讨论！

---

**（本 README 结合代码结构与关键实现，适合初学者和进阶用户快速上手和二次开发）**



