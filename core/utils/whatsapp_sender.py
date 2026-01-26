"""
WhatsApp 发送器 - 使用 CallMeBot API 发送真实 WhatsApp 消息
"""
import requests
import urllib.parse
from django.conf import settings


def send_real_whatsapp(message):
    """
    发送真实 WhatsApp 消息 (依赖 CallMeBot 免费 API)
    
    Args:
        message (str): 要发送的消息内容
    
    Returns:
        None: 静默返回，不抛出异常
    """
    if not getattr(settings, 'WHATSAPP_ENABLED', False):
        return

    phone = getattr(settings, 'WHATSAPP_PHONE', '')
    apikey = getattr(settings, 'WHATSAPP_API_KEY', '')

    # 简单的校验：如果没有配置 phone 或 key，就不发
    if not phone or not apikey or apikey == "WAITING_FOR_KEY":
        print(f"⚠️ [WhatsApp] Config missing or Key not ready. Msg skipped: {message[:20]}...")
        return

    print(f"📨 [WhatsApp] Sending to {phone}...")

    try:
        # 构造 URL 参数
        params = {
            'phone': phone,
            'text': message,
            'apikey': apikey
        }
        
        # 发送 GET 请求
        response = requests.get("https://api.callmebot.com/whatsapp.php", params=params, timeout=10)
        
        if response.status_code == 200:
            print("✅ [WhatsApp] Sent Successfully!")
        else:
            print(f"❌ [WhatsApp] Failed: {response.text}")

    except Exception as e:
        print(f"❌ [WhatsApp] Connection Error: {e}")
