import math
import os
import json
import requests
import openai

# from dotenv import load_dotenv, find_dotenv
# _ = load_dotenv(find_dotenv())  # read local .env file
# openai.api_key = os.environ['OPENAI_API_KEY']

def calculate_cylinder_volume(radius, height):
    """
    Calculate the volume of a cylinder using the formula:
    Volume = π * r^2 * h
    """
    if radius <= 0 or height <= 0:
        return "Radius and height must be positive numbers."
    
    volume = math.pi * (radius ** 2) * height
    return round(volume, 2)


cylinder_function = {
    "name": "calculate_cylinder_volume",
    "description": "Calculate the volume of a cylinder given radius and height.",
    "parameters": {
        "type": "object",
        "properties": {
            "radius": {"type": "number", "description": "Radius of the cylinder (in units)"},
            "height": {"type": "number", "description": "Height of the cylinder (in units)"},
        },
        "required": ["radius", "height"],
    },
}

def chat_with_llm(prompt, **llm_config):
    """根据配置调用不同的 LLM 模型"""
    model = llm_config.get("model", "deepseek-chat")
    base_url = llm_config.get("base_url", "https://api.deepseek.com")
    api_key = llm_config.get("api_key", "YOUR_API_KEY")

    # 系统提示词,引导模型使用 function call
    system_prompt = """你是一个助手,主要帮助用户计算圆柱体体积。当用户询问圆柱体体积相关问题时,
    请优先使用 function call 来调用 calculate_cylinder_volume 函数进行计算。
    函数参数说明:
    - radius: 圆柱体的半径
    - height: 圆柱体的高度
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # 根据不同模型调用API
    try:
        if "gpt" in model.lower():
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                functions=[cylinder_function],
                function_call="auto",
            )
        elif "claude" in model.lower():
            response = requests.post(
                f"{base_url}/v1/complete",
                headers={"x-api-key": api_key},
                json={
                    "model": model,
                    "messages": messages,
                    "functions": [cylinder_function],
                    "function_call": "auto",
                }
            ).json()
        elif "deepseek" in model.lower() or "qwen" in model.lower():
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "functions": [cylinder_function],
                    "function_call": "auto",
                }
            ).json()
        else:
            raise ValueError(f"不支持的模型: {model}")

        # 检查是否使用了function call
        if "choices" in response and "message" in response["choices"][0]:
            message = response["choices"][0]["message"]
            
            if "function_call" in message:
                # 使用function call的情况
                try:
                    function_name = message["function_call"]["name"]
                    arguments = json.loads(message["function_call"]["arguments"])
                    
                    if function_name == "calculate_cylinder_volume":
                        radius = float(arguments["radius"])
                        height = float(arguments["height"])
                        result = calculate_cylinder_volume(radius, height)
                        return f"通过function call计算: 半径为{radius},高度为{height}的圆柱体体积是{result}立方单位。"
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    print(f"Function call解析失败: {str(e)}")
                    return "Function call解析失败,请重试。"
            else:
                # 未使用function call的情况,直接返回LLM的回答
                return message.get("content", "请明确提供圆柱体的半径和高度。")
                
    except Exception as e:
        return f"API调用出错: {str(e)}"

    return "无法处理您的请求,请重试。"




# llm_config = {
#     "model": "deepseek-chat",  # 可以是 "gpt-4", "claude", "qwen2.5-72b-instruct", "deepseek-chat"
#     "base_url": "https://api.deepseek.com/v1",  # 根据选择的模型调整
#     "api_key": "sk-3b458ee0624f41e1b8c589e74be23e44"  # 根据选择的模型调整
# }

llm_config = {
    "model": "Qwen/Qwen2.5-72B-Instruct",  # 可以是 "gpt-4", "claude", "qwen2.5-72b-instruct", "deepseek-chat"
    "base_url": "https://api.siliconflow.cn/v1",  # 根据选择的模型调整
    "api_key": "sk-ykbiglqspirbapnzjvrasbuhboizzqhhhjupwcwxkvhcktod"  # 根据选择的模型调整
}



if __name__ == "__main__":
    radius = float(input("Enter the radius of the cylinder: "))
    height = float(input("Enter the height of the cylinder: "))

    prompt = f"""What is the volume of a cylinder-type container
    with a radius of {radius}cm and a height of {height}cm?
    """
    result = chat_with_llm(prompt, **llm_config)
    print("Result:", result)
