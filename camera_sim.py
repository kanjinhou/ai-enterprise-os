"""
摄像头模拟器 - 模拟 AI 摄像头向服务器发送 PPE 检测数据
"""
import requests
import random
import json
import time

# ============ 配置 ============
API_URL = 'http://127.0.0.1:8000/api/v1/ppe/events/'
USERNAME = 'admin'
PASSWORD = 'admin123'
IMAGE_PATH = 'test.png'

# 可选的摄像头 ID
CAMERA_IDS = ['CAM-01', 'CAM-02', 'CAM-03']

# 可选的违规类型
VIOLATION_TYPES = ['no_helmet', 'no_vest', 'no_gloves', 'no_goggles']


def generate_random_detection():
    """生成随机的检测数据"""
    return {
        'violation': random.choice(VIOLATION_TYPES),
        'confidence': round(random.uniform(0.85, 0.99), 2),
        'bbox': [
            random.randint(0, 100),
            random.randint(0, 100),
            random.randint(100, 300),
            random.randint(100, 300)
        ]
    }


def send_detection_event():
    """发送一次检测事件到服务器"""
    # 随机选择摄像头
    camera_id = random.choice(CAMERA_IDS)
    
    # 生成随机检测数据
    detections = generate_random_detection()
    
    # 准备表单数据
    data = {
        'camera_id': camera_id,
        'detections': json.dumps(detections),  # JSON 字段需要序列化为字符串
    }
    
    try:
        # 打开图片文件
        with open(IMAGE_PATH, 'rb') as image_file:
            files = {
                'image': ('detection.jpg', image_file, 'image/jpeg')
            }
            
            # 发送 POST 请求
            response = requests.post(
                API_URL,
                data=data,
                files=files,
                auth=(USERNAME, PASSWORD)  # Basic Auth
            )
        
        # 打印结果
        print(f"[{time.strftime('%H:%M:%S')}] Camera: {camera_id}")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 201:
            print(f"  Success! Event ID: {response.json().get('id')}")
        else:
            print(f"  Response: {response.text[:200]}")
        
        print("-" * 50)
        return response.status_code == 201
        
    except FileNotFoundError:
        print(f"Error: 找不到图片文件 '{IMAGE_PATH}'")
        print("请确保在脚本同目录下有一张 test.jpg 图片")
        return False
    except requests.exceptions.ConnectionError:
        print("Error: 无法连接到服务器")
        print("请确保 Django 服务器正在运行: python manage.py runserver")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """主函数 - 循环发送检测事件"""
    print("=" * 50)
    print("PPE 摄像头模拟器启动")
    print(f"API: {API_URL}")
    print(f"User: {USERNAME}")
    print("=" * 50)
    print()
    
    # 循环 5 次用于测试 (改成 while True 可以持续运行)
    for i in range(5):
        print(f"发送第 {i + 1} 次检测事件...")
        success = send_detection_event()
        
        if not success:
            print("发送失败，停止模拟")
            break
        
        # 休息 3 秒
        time.sleep(3)
    
    print("\n模拟结束!")


if __name__ == '__main__':
    main()
