"""
LLM 辅助工具
用于生成简短的安全建议（实时报警场景）
"""
import requests
import json
from django.conf import settings


def get_safety_advice(violation_type, camera_name):
    """
    调用 LLM API 生成一句话安全建议
    
    Args:
        violation_type (str): 违规类型，例如 "no_helmet", "no_vest" 等
        camera_name (str): 摄像头名称，例如 "CAM-01"
    
    Returns:
        str: 一句简短、专业的英文安全建议，如果 API 调用失败则返回默认建议
    """
    prompt = f"You are a Safety Officer. A '{violation_type}' violation was detected at '{camera_name}'. Give ONE short, professional sentence of advice to the supervisor. English only."

    # 获取配置
    api_key = getattr(settings, 'LLM_API_KEY', None)
    api_base = getattr(settings, 'LLM_API_BASE', 'https://api.openai.com/v1')
    model = getattr(settings, 'LLM_MODEL', 'llama3.2')
    
    # 构建请求 URL
    api_url = f"{api_base.rstrip('/')}/chat/completions"
    
    # 准备 payload（兼容 OpenAI/DeepSeek 和 Ollama）
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }
    
    # 准备 headers（如果有 API key，则使用 Bearer token；否则适用于本地 Ollama）
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # 兼容不同的响应格式
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '').strip()
                if content:
                    return content
    except requests.exceptions.Timeout:
        print(f"⚠️ AI Advice Failed: Timeout (10s exceeded)")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ AI Advice Failed: {e}")
    except Exception as e:
        print(f"⚠️ AI Advice Failed: {e}")
    
    # 默认建议
    return "Please verify safety compliance immediately."
