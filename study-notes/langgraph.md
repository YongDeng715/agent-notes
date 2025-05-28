# LangChain + LangGraph notes

## Reference

1. [LangChain Python API Reference](https://python.langchain.com/api_reference/reference.html)
    - [create_react_agent](https://python.langchain.com/api_reference/langchain/agents/langchain.agents.react.agent.create_react_agent.html)
    - []
2. [LangGraph Study Guide](https://github.langchain.ac.cn/langgraph/)


## ReAct Agent


example code, from [LangGraph agents](https://langchain-ai.github.io/langgraph/reference/agents/)
该代码样例也可以在 langgraph 源码里找到

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

def check_weather(location: str) -> str:
    '''Return the weather forecast for the specified location.'''
    return f"It's always sunny in {location}"

model = ChatOpenAI(model="gpt-4o")
system_prompt = "You are a helpful bot named Fred."

graph = create_react_agent(
    model=model,
    tools=[check_weather],
    rompt=system_prompt
)

inputs = {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
for chunk in graph.stream(inputs, stream_mode="updates"):
    print(chunk)
```


## Construct a Graph

### add_adge & add_conditional_adge


### Command

将控制流（边）和状态更新（节点）结合起来可能会很有用。例如，可能希望在同一个节点中既执行状态更新又决定下一步前往哪个节点。LangGraph 提供了一种方法，即从节点函数返回一个 `Command` 对象。

```python
def my_node(state: State) -> Command[Literal["my_other_node"]]:
    return Command(
        # state update
        update={"foo": "bar"},
        # control flow
        goto="my_other_node"
    )
```
使用 Command，还可以实现动态控制流行为（与条件边相同）

```python
def my_node(state: State) -> Command[Literal["my_other_node"]]:
    if state["foo"] == "bar":
        return Command(update={"foo": "baz"}, goto="my_other_node")
```

需要同时更新图状态并路由到不同的节点时，使用 `Command`
如果正在使用子图，希望从子图中的一个节点导航到另一个子图（即父图中的不同节点）。可以在 `Command` 中指定 `graph=Command.PARENT`

```python
def my_node(state: State) -> Command[Literal["other_subgraph"]]:
    return Command(
        update={"foo": "bar"},
        goto="other_subgraph",  # where `other_subgraph` is a node in the parent graph
        graph=Command.PARENT
    )
```



### stream

```python
stream(
    input: dict[str, Any] | Any,
    config: RunnableConfig | None = None,
    *,
    stream_mode: (
        StreamMode | list[StreamMode] | None
    ) = None,
    output_keys: str | Sequence[str] | None = None,
    interrupt_before: All | Sequence[str] | None = None,
    interrupt_after: All | Sequence[str] | None = None,
    checkpoint_during: bool | None = None,
    debug: bool | None = None,
    subgraphs: bool = False
) -> Iterator[dict[str, Any] | Any]
```

select `stream_mode`

```python
import operator
from typing_extensions import Annotated, TypedDict
from langgraph.graph import StateGraph, START

class State(TypedDict):
    alist: Annotated[list, operator.add]
    another_list: Annotated[list, operator.add]

builder = StateGraph(State)
builder.add_node("a", lambda _state: {"another_list": ["hi"]})
builder.add_node("b", lambda _state: {"alist": ["there"]})
builder.add_edge("a", "b")
builder.add_edge(START, "a")
graph = builder.compile()

for event in graph.stream({"alist": ['Ex for stream_mode="values"']}, stream_mode="values"):
    print(event)

# {'alist': ['Ex for stream_mode="values"'], 'another_list': []}
# {'alist': ['Ex for stream_mode="values"'], 'another_list': ['hi']}
# {'alist': ['Ex for stream_mode="values"', 'there'], 'another_list': ['hi']}

for event in graph.stream({"alist": ['Ex for stream_mode="updates"']}, stream_mode="updates"):
    print(event)

# {'a': {'another_list': ['hi']}}
# {'b': {'alist': ['there']}}

for event in graph.stream({"alist": ['Ex for stream_mode="debug"']}, stream_mode="debug"):
    print(event)

# {'type': 'task', 'timestamp': '2024-06-23T...+00:00', 'step': 1, 'payload': {'id': '...', 'name': 'a', 'input': {'alist': ['Ex for stream_mode="debug"'], 'another_list': []}, 'triggers': ['start:a']}}
# {'type': 'task_result', 'timestamp': '2024-06-23T...+00:00', 'step': 1, 'payload': {'id': '...', 'name': 'a', 'result': [('another_list', ['hi'])]}}
# {'type': 'task', 'timestamp': '2024-06-23T...+00:00', 'step': 2, 'payload': {'id': '...', 'name': 'b', 'input': {'alist': ['Ex for stream_mode="debug"'], 'another_list': ['hi']}, 'triggers': ['a']}}
# {'type': 'task_result', 'timestamp': '2024-06-23T...+00:00', 'step': 2, 'payload': {'id': '...', 'name': 'b', 'result': [('alist', ['there'])]}}

```
