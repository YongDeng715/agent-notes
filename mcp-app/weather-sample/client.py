"""
实现 Weather Client by OpenAI/Qwen/Deepseek API
原文链接： https://blog.csdn.net/fufan_LLM/article/details/146377471
"""

import asyncio
import os
import json
from typing import Optional
from contextlib import AsyncExitStack
 
from openai import OpenAI  
from dotenv import load_dotenv
 
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
 
#### 直接声明变量
OPENAI_API_KEY = "sk-ykbiglqspirbapnzjvrasbuhboizzqhhhjupwcwxkvhcktod" 
BASE_URL = "https://api.siliconflow.cn/v1"        
MODEL = "Qwen/Qwen2.5-72B-Instruct"           

# OPENAI_API_KEY = "EMPTY_API_KEY"  # 在这里直接设置您的 OpenAI API Key
# BASE_URL = "http://111.12.146.19:32430/v1"        # 在这里直接设置您的 Base URL
# MODEL = "qwen2.5-instruct"           # 在这里直接设置您的 Model
TEMPERATURE = 0.7       # 添加温度参数
MAX_TOKENS = 2048       # 添加最大token数

# 加载 .env 文件，确保 API Key 受到保护
load_dotenv()
 
class MCPClient:
    def __init__(self):
        """初始化 MCP 客户端"""
        self.exit_stack = AsyncExitStack()
        # 优先使用直接声明的变量，如果为空则从 .env 文件读取
        self.openai_api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.base_url = BASE_URL or os.getenv("BASE_URL")
        self.model = MODEL or os.getenv("MODEL")
        self.temperature = TEMPERATURE or float(os.getenv("TEMPERATURE", 0.9))
        self.max_tokens = MAX_TOKENS or int(os.getenv("MAX_TOKENS", 2048))
        
        if not self.openai_api_key:
            raise ValueError("❌ 未找到 OpenAI API Key，请在 .env 文件中设置 OPENAI_API_KEY 或在代码顶部直接声明")
        
        # 创建 OpenAI client，支持本地部署的模型
        self.client = OpenAI(
            api_key=self.openai_api_key,
            base_url=self.base_url,
            timeout=30.0  # 增加超时时间，因为本地模型可能响应较慢
        )
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()        
 
    async def connect_to_server(self, server_script_path: str):
        """连接到 MCP 服务器并列出可用工具"""
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("服务器脚本必须是 .py 或 .js 文件")
 
        command = "python"if is_python else"node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
 
        # 启动 MCP 服务器并建立通信
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
 
        await self.session.initialize()
 
        # 列出 MCP 服务器上的工具
        response = await self.session.list_tools()
        tools = response.tools
        print("\n已连接到服务器，支持以下工具:", [tool.name for tool in tools])     
        
    async def process_query(self, query: str) -> str:
        """
        使用大模型处理查询并调用可用的 MCP 工具 (Function Calling)
        """
        messages = [{"role": "user", "content": query}]
        
        response = await self.session.list_tools()
        
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema  # 修改为 parameters 以兼容更多模型
            }
        } for tool in response.tools]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,            
                messages=messages,
                tools=available_tools,
                temperature=self.temperature,  
                max_tokens=self.max_tokens   
            )
            
            # 处理返回的内容
            content = response.choices[0]
            if content.finish_reason == "tool_calls":
                # 如何是需要使用工具，就解析工具
                tool_call = content.message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # 执行工具
                result = await self.session.call_tool(tool_name, tool_args)
                print(f"\n\n[Calling tool {tool_name} with args {tool_args}]\n\n")
                
                # 将模型返回的调用哪个工具数据和工具执行完成后的数据都存入messages中
                messages.append(content.message.model_dump())
                messages.append({
                    "role": "tool",
                    "content": result.content[0].text,
                    "tool_call_id": tool_call.id,
                })
                
                # 将上面的结果再返回给大模型用于生产最终的结果
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content
                
            return content.message.content
            
        except Exception as e:
            print(f"\n⚠️ 模型调用错误: {str(e)}")
            return f"模型调用出错: {str(e)}"
    
    async def chat_loop(self):
        """运行交互式聊天循环"""
        print("\n🤖 MCP 客户端已启动！输入 'quit' 退出")
        print(f"当前使用的模型: {self.model}")
        print(f"API 地址: {self.base_url}")
 
        while True:
            try:
                query = input("\n用户询问: ").strip()
                if query.lower() == 'quit':
                    break
                
                response = await self.process_query(query)
                print(f"\n🤖 {self.model}: {response}")
 
            except Exception as e:
                print(f"\n⚠️ 发生错误: {str(e)}")
 
    async def cleanup(self):
        """清理资源"""
        await self.exit_stack.aclose()
 
async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
 
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()
 
if __name__ == "__main__":
    import sys
    asyncio.run(main())