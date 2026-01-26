"""
通知服务层 - 处理实时报警（WhatsApp、Email、SMS 等）
目前为模拟实现，预留真实 API 接入位置
"""
import os
from dotenv import load_dotenv

# 强制读取 .env 文件（无论在哪里运行都能读到）
load_dotenv()

from django.conf import settings
from core.utils.llm_helper import get_safety_advice
from core.utils.whatsapp_sender import send_real_whatsapp


class NotificationService:
    """
    通知服务类 - 统一管理各种通知渠道
    目前支持：WhatsApp（模拟）
    未来扩展：Email、SMS、Telegram、Slack 等
    """
    
    @staticmethod
    def _extract_violation_details(detections):
        """
        从 detections JSON 中提取违规详情
        返回可读的违规类型描述
        """
        if not isinstance(detections, dict):
            return "Unknown violation"
        
        # 尝试从 items 数组中提取
        items = detections.get("items", [])
        if items and isinstance(items, list):
            violation_types = []
            for item in items:
                if isinstance(item, dict):
                    v_type = item.get("class") or item.get("violation")
                    if v_type:
                        # 转换为可读格式：no_helmet -> No Helmet
                        readable = str(v_type).replace("_", " ").title()
                        violation_types.append(readable)
            if violation_types:
                return ", ".join(violation_types)
        
        # 尝试直接获取 violation 或 class
        violation = detections.get("violation") or detections.get("class")
        if violation:
            return str(violation).replace("_", " ").title()
        
        return "Safety violation detected"
    
    @staticmethod
    def send_whatsapp_alert(event):
        """
        发送 WhatsApp 报警消息
        
        Args:
            event: DetectionEvent 对象
        
        目前为模拟实现，打印到控制台
        未来可替换为 Twilio / WhatsApp Business API
        """
        # 提取违规详情
        violation_details = NotificationService._extract_violation_details(event.detections)
        
        # 调用 AI 生成安全建议
        try:
            advice = get_safety_advice(violation_details, event.camera_id)
        except Exception as e:
            print(f"[Notification] Failed to get AI advice: {e}")
            advice = "Please verify safety compliance immediately."
        
        # 格式化时间
        time_str = event.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        # 构造消息内容（包含 AI 建议，纯文本格式）
        message = f"""SECURITY ALERT!
Type: {violation_details}
Camera: {event.camera_id}
Time: {time_str}
Customer: {event.customer.name}
AI Advice: {advice}"""
        
        # ========== 模拟发送（当前实现）==========
        log_message = f"[WhatsApp] Sending to Manager: SECURITY ALERT! Type: {violation_details}"
        # 如果识别到员工身份，添加到日志中
        if hasattr(event, 'person_name') and event.person_name and event.person_name != "Unknown":
            log_message += f". Employee: {event.person_name}"
            if hasattr(event, 'person_id') and event.person_id and event.person_id != "N/A":
                log_message += f" (ID: {event.person_id})"
        log_message += f". AI Advice: {advice}"
        print(log_message)
        print(f"[WhatsApp] Image URL: {event.image.url if event.image else 'N/A'}")
        print(f"[WhatsApp] Event ID: {event.id}")
        print("-" * 60)
        
        # ========== 真实 WhatsApp 发送（CallMeBot API）==========
        # 构造简洁的报警消息（用于 WhatsApp 发送，纯文本格式，无 Emoji）
        alert_message = f"SAFETY ALERT!\nType: {violation_details}\nCamera: {event.camera_id}\nTime: {time_str}"
        
        # 如果识别到员工身份，添加到消息中
        if hasattr(event, 'person_name') and event.person_name and event.person_name != "Unknown":
            alert_message += f"\nEmployee: {event.person_name}"
            if hasattr(event, 'person_id') and event.person_id and event.person_id != "N/A":
                alert_message += f" (ID: {event.person_id})"
        
        alert_message += f"\nAdvice: {advice}"
        
        # 调用真实 WhatsApp 发送函数（CallMeBot）
        try:
            send_real_whatsapp(alert_message)
        except Exception as e:
            # 即使真实发送失败，也不影响事件保存
            print(f"[Notification] Failed to send real WhatsApp: {e}")
        
        # ========== Twilio WhatsApp Business API ==========
        try:
            from twilio.rest import Client
            
            # 1. 获取配置（从 .env 文件读取，已在文件开头通过 load_dotenv() 加载）
            sid = os.environ.get('TWILIO_ACCOUNT_SID')
            token = os.environ.get('TWILIO_AUTH_TOKEN')
            from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
            to_number = os.environ.get('MY_PHONE_NUMBER')
            
            # 检查配置
            if not all([sid, token, from_number, to_number]):
                print(f"[WARNING] Twilio config missing in .env. SID found: {bool(sid)}, Token found: {bool(token)}, From found: {bool(from_number)}, To found: {bool(to_number)}")
                return True
            
            client = Client(sid, token)
            
            # 2. 构建消息（纯文本格式，无 Emoji，避免 Windows latin-1 编码错误）
            # 提取违规类型、人员信息
            title = violation_details
            person_name = getattr(event, 'person_name', 'Unknown')
            person_id = getattr(event, 'person_id', 'N/A')
            description = f"Camera: {event.camera_id} | Time: {time_str}"
            
            # 构建纯文本消息（无 Emoji）
            msg_body = f"SECURITY ALERT\n\nType: {title}\nEmployee: {person_name} (ID: {person_id})\nDescription: {description}\nAdvice: {advice}"
            
            # 3. 准备图片 URL（如果存在）
            media_urls = []
            if hasattr(event, 'image') and event.image:
                # 定义 Ngrok 域名（注意结尾不要带斜杠）
                base_url = "https://unmelodramatic-shena-radioactively.ngrok-free.dev"
                
                # 获取图片的相对路径
                image_url = event.image.url
                
                # 拼接完整图片链接
                full_image_url = f"{base_url}{image_url}"
                media_urls = [full_image_url]
                print(f"[INFO] Image Link: {full_image_url}")
            
            # 4. 发送消息（带图片，如果有）
            message_params = {
                'body': msg_body,
                'from_': from_number,
                'to': to_number
            }
            
            # 如果有图片，添加 media_url 参数
            if media_urls:
                message_params['media_url'] = media_urls
            
            message = client.messages.create(**message_params)
            print(f"[SUCCESS] WhatsApp Sent via Twilio! SID: {message.sid}")
            
        except ImportError:
            print("[WARNING] Twilio library not installed. Install with: pip install twilio")
        except Exception as e:
            # 错误日志也不能包含 Emoji
            print(f"[ERROR] WhatsApp Error (Twilio): {e}")
        
        return True
    
    @staticmethod
    def send_email_alert(event):
        """
        发送邮件报警（预留接口）
        """
        # TODO: 实现邮件发送逻辑
        pass
    
    @staticmethod
    def send_sms_alert(event):
        """
        发送短信报警（预留接口）
        """
        # TODO: 实现短信发送逻辑
        pass
