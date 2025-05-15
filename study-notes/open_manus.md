# OpenManus

github: https://github.com/FoundationAgents/OpenManus


Openmanus整体结构的讲解

```bash
OpenManus
├── Agent (代理层)
│   ├── BaseAgent (基础抽象类)
│   ├── ReActAgent (思考-行动模式)
│   ├── ToolCallAgent (工具调用能力)
│   ├── SWEAgent (软件工程能力)
│   └── Manus (通用代理)
├── LLM (语言模型层)
├── Memory (记忆层)
├── Tool (工具层)
│   ├── BaseTool (工具基类)
│   ├── PlanningTool (规划工具)
│   ├── PythonExecute (Python 执行)
│   ├── GoogleSearch (搜索工具)
│   ├── BrowserUseTool (浏览器工具)
│   └── ... (其他工具)
├── Flow (工作流层)
│   ├── BaseFlow (基础流程)
│   └── PlanningFlow (规划流程)
└── Prompt (提示词层)
```

