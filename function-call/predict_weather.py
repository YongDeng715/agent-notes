import re
import json
from typing import Dict
import aiohttp

class LLMClient:
    def __init__(self, model_name: str, api_key: str, base_url: str):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url

    async def call_llm(self, prompt: str) -> str:
        """调用 LLM 模型"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.3
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/completions", headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        response_json = await resp.json()
                        # 假设返回的 JSON 格式为 {"choices": [{"text": "返回的文本"}]}
                        return response_json["choices"][0]["text"]
                    else:
                        error_message = await resp.text()
                        return json.dumps({"error": f"请求失败，状态码: {resp.status}, 错误信息: {error_message}"})
        except Exception as e:
            return json.dumps({"error": f"请求过程中发生异常: {str(e)}"})

class WeatherAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def get_weather_info(self, prompt: str) -> Dict:
        """获取指定城市的天气信息"""
        # 让 LLM 解析城市和天数
        analysis_prompt = f"""
        请从以下用户输入中提取出城市名称和需要的天气天数：
        输入: "{prompt}"
        返回格式: {{"city": "城市名称", "days": 天数}}
        注意: 天数应为小于8的整数，城市名称为字符串。
        """
        
        analysis_response = await self.llm_client.call_llm(analysis_prompt)
        try:
            analysis_data = json.loads(analysis_response)
        except json.JSONDecodeError:
            return {"error": "无法解析 LLM 返回的数据"}

        city = analysis_data.get("city", "未知城市")
        days = analysis_data.get("days", 0)
        
        if days < 1 or days > 7:
            return {"error": "天数必须在1到7之间"}
        
        # 构建天气信息请求的提示词
        weather_prompt = f"""
        作为一个专业的天气信息提供者，请提供 {city} 的详细天气信息。
        请确保所有数据都是准确的，并按照以下格式返回：

        1. 当前时间：
           - 使用北京时间（UTC+8）
           - 格式：YYYY-MM-DD HH:MM:SS

        2. 当前天气状况：
           - 温度：摄氏度，精确到小数点后1位
           - 天气状况：使用标准天气描述（如：晴、多云、小雨等）
           - 湿度：整数百分比（0-100）
           - 风速：公里/小时，精确到小数点后1位

        3. 未来{days}天天气预报：
           - 从今天开始，连续{days}天
           - 每天包含：日期、最高温度、最低温度、天气状况
           - 温度单位：摄氏度
           - 天气状况：使用标准天气描述

        请严格按照以下 JSON 格式返回数据：
        {{
            "current_time": "2024-03-21 14:30:00",
            "current_weather": {{
                "temperature": 25.5,
                "condition": "多云",
                "humidity": 65,
                "wind_speed": 12.5
            }},
            "forecast": [
                {{
                    "date": "2024-03-21",
                    "max_temp": 28.0,
                    "min_temp": 18.5,
                    "condition": "多云转晴"
                }},
                // ... 未来{days-1}天
            ]
        }}

        注意：
        1. 所有数值必须是数字，不要使用字符串
        2. 日期格式必须统一为 YYYY-MM-DD
        3. 天气状况使用标准中文描述
        4. 确保数据合理性和一致性
        """

        response = await self.llm_client.call_llm(weather_prompt)
        return self._parse_weather_data(response)

    def _parse_weather_data(self, weather_data: str) -> Dict:
        """解析 LLM 返回的天气数据"""
        try:
            data = json.loads(weather_data)
            
            # 数据验证和清理
            if not isinstance(data.get("current_weather", {}).get("temperature"), (int, float)):
                raise ValueError("温度必须是数字")
                
            if not isinstance(data.get("current_weather", {}).get("humidity"), int):
                raise ValueError("湿度必须是整数")
                
            if len(data.get("forecast", [])) < 1:
                raise ValueError("必须提供至少一天的天气预报")
                
            return data
        except Exception as e:
            return {"error": f"解析天气数据失败: {str(e)}"}

# 异步调用示例
async def main():
    # 使用一个本地部署的 Qwen2.5 AWQ模型
    model_name = "qwen2.5-instruct"
    api_key = "EMPTY"
    base_url = "http://111.12.146.19:32430/v1"
    llm_client = LLMClient(model_name, api_key, base_url)
    
    weather_agent = WeatherAgent(llm_client)
    prompt = "武汉未来3天的天气情况"
    
    weather_info = await weather_agent.get_weather_info(prompt)
    print(weather_info)

# 运行异步函数
import asyncio
asyncio.run(main()) 