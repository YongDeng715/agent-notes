import requests
import json
import re
import random
import asyncio
import aiohttp
from datetime import datetime

# 配置API密钥
DEEPSEEK_API_KEY = "sk-3b458ee0624f41e1b8c589e74be23e44"
OPENWEATHER_API_KEY = "YOUR_API_KEY"

# Function Definitions (JSON Schema格式)
functions = [
    {
        "name": "get_current_weather",
        "description": "获取指定城市的当前天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称，如：'北京' 或 'London'"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "ask_deepseek",
        "description": "回答通用问题，涉及知识查询、建议、解释概念等",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "用户提出的问题或请求"
                }
            },
            "required": ["question"]
        }
    }
]

async def call_function(function_name, arguments):
    """路由函数调用到具体实现"""
    if function_name == "get_current_weather":
        return await get_current_weather(
            location=arguments.get("location"),
            unit=arguments.get("unit", "celsius")
        )
    elif function_name == "ask_deepseek":
        return await ask_deepseek(
            question=arguments.get("question")
        )
    else:
        return "未找到对应功能"


# OpenWeather API实现
async def get_current_weather(location, unit="celsius"):
    # 检查是否配置了API密钥
    if OPENWEATHER_API_KEY and OPENWEATHER_API_KEY != "YOUR_API_KEY":
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": location,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric" if unit == "celsius" else "imperial"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if response.status == 200:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        weather_info = {
                            "location": data["name"],
                            "temperature": data["main"]["temp"],
                            "unit": "°C" if unit == "celsius" else "°F",
                            "description": data["weather"][0]["description"],
                            "humidity": f"{data['main']['humidity']}%",
                            "wind_speed": f"{data['wind']['speed']} m/s",
                            "date": current_time,
                            "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M:%S"),
                            "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M:%S")
                        }
                        return json.dumps(weather_info)
                    else:
                        print(f"获取天气信息失败：使用模拟数据")
                        return await mock_weather_data(location, unit)
        except Exception as e:
            print(f"天气API调用异常：{str(e)}，使用模拟数据")
            return await mock_weather_data(location, unit)
    else:
        print("未配置天气API密钥：使用模拟数据")
        return await mock_weather_data(location, unit)

async def mock_weather_data(location, unit="celsius"):
    """模拟天气数据"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    weather_info = {
        "location": location,
        "temperature": round(random.uniform(18, 35), 1),
        "unit": "°C" if unit == "celsius" else "°F",
        "description": random.choice(["晴", "多云", "阴", "小雨", "中雨", "大雨"]),
        "humidity": f"{random.randint(50, 80)}%",
        "wind_speed": f"{round(random.uniform(5, 15), 1)} m/s",
        "date": current_time,
        "sunrise": "06:00:00",
        "sunset": "18:00:00"
    }
    return json.dumps(weather_info)



# DeepSeek API实现
async def ask_deepseek(question):
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": question}],
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"DeepSeek API错误：{data.get('error', {}).get('message', '未知错误')}"
    
    except Exception as e:
        return f"DeepSeek API调用异常：{str(e)}"

async def process_query(user_query):
    """处理用户查询的主函数, 首先使用LLM进行意图识别, 然后根据意图调用对应的函数"""
    response = await detect_intent(user_query)
    print(response)

    if response["function"] == "get_current_weather":
        return await call_function("get_current_weather", {
            "location": response["parameters"]["location"],
            "unit": "celsius"
        })
    else:
        return await call_function("ask_deepseek", {
            "question": user_query
        })

async def detect_intent(query):
    prompt = f"""判断用户意图并返回JSON：
    {{
        "function": "get_current_weather" | "ask_deepseek",
        "parameters": {{...}}
    }}
    
    示例：
    输入：北京天气怎么样？
    输出：{{"function": "get_current_weather", "parameters": {{"location": "北京"}}}}
    
    当前输入：{query}"""
    
    response = await ask_deepseek(prompt)

    try:
        # 如果response已经是字典格式,直接返回
        if isinstance(response, dict):
            return response
            
        # 如果response是markdown格式的JSON字符串,进行解析
        def parse_markdown_json(md_str):
            cleaned_str = re.sub(r'^```json\s*|```$', '', md_str, flags=re.DOTALL).strip()
            return json.loads(cleaned_str)
        return parse_markdown_json(response)
    except Exception as e:
        print(f"解析响应失败: {str(e)}")
        # 解析失败时返回默认响应
        return {
            "function": "ask_deepseek",
            "parameters": {"question": query}
        }


# 2. 添加单位自动转换
def convert_temperature(temp, from_unit, to_unit):
    if from_unit == to_unit:
        return temp
    if from_unit == "celsius" and to_unit == "fahrenheit":
        return (temp * 9/5) + 32
    else:
        return (temp - 32) * 5/9

# 添加缓存机制
from functools import lru_cache
@lru_cache(maxsize=100)
async def cached_weather(location, unit):
    return await get_current_weather(location, unit)



async def main(queries):
    for query in queries:
        print(f"用户问：{query}")
        response = await process_query(query)
        
        # 尝试解析JSON响应（适用于天气API）
        try:
            weather_data = json.loads(response)
            print("天气信息：")
            print(f"城市：{weather_data['location']}")
            print(f"日期时间：{weather_data['date']}")
            print(f"温度：{weather_data['temperature']}{weather_data['unit']}")
            print(f"天气状况：{weather_data['description']}")
            print(f"湿度：{weather_data['humidity']}")
            print(f"风速：{weather_data['wind_speed']}")
            print(f"日出时间：{weather_data['sunrise']}")
            print(f"日落时间：{weather_data['sunset']}\n")
        except:
            print(f"回答：{response}\n")


# 使用示例
if __name__ == "__main__":
    queries = [
        "北京现在的天气怎么样？",
        "我的家乡在武汉，我家乡城市今天的天气情况是怎样的",
        "上海今天的温度",
        "我女朋友在厦门，我想知道当地天气情况",
        "请解释量子计算的基本原理？"
    ]
    
    asyncio.run(main(queries))
