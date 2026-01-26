"""
DJI 无人机控制服务
用于触发无人机任务（Trespasser Alert）
"""
import requests
import json
import traceback

# ================= 配置区域 =================
DJI_API_URL = "https://es-flight-api-us.djigate.com/openapi/v0.1/workflow"
# 注意：这里是用户提供的真实 Token，用于演示
DJI_TOKEN = "eyJhbGciOiJIUzUxMiIsImNyaXQiOlsidHlwIiwiYWxnIiwia2lkIl0sImtpZCI6IjBkNzQyMzFmLTgxOWYtNDE3NS04NWUzLTRhZDQxODUzMzEyZiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50IjoiYWl6YXRAZ2xvY29tcC5uZXQiLCJleHAiOjIwODMzOTA2NzcsIm5iZiI6MTc2Nzg1Nzg3Nywib3JnYW5pemF0aW9uX3V1aWQiOiI3OTlmMzYxYS0yY2MwLTQ5MTEtOGRlNy1jZDM1NDhlZTMwYTEiLCJwcm9qZWN0X3V1aWQiOiIiLCJzdWIiOiJmaDIiLCJ1c2VyX2lkIjoiMTg5NzE4Nzg0NjI3NDMxMDE0NCJ9.eCgjxdiOxtFT_dPNUDHGiuun_isj4bjc2MEl3nKYtDAMpsg7T9BeA20u0K6vUwE-LVHjti5aNf8SyRKPZvXY4w"
PROJECT_UUID = "793e4874-96b0-4a37-8b32-9b1a5f28d4dc"
WORKFLOW_UUID = "e143d3e7-445f-4fd7-a721-a5d449e63854"


def trigger_mission():
    """
    触发无人机任务（Trespasser Alert）
    
    Returns:
        dict: {"status": "success"/"error", "msg": "...", "data": ...}
    """
    headers = {
        'Content-Type': 'application/json',
        'X-User-Token': DJI_TOKEN,
        'x-project-uuid': PROJECT_UUID
    }
    payload_data = {
        "workflow_uuid": WORKFLOW_UUID,
        "trigger_type": 0,
        "name": "Alert-20250101010800",
        "params": {
            "creator": "1841363730749616128",
            "latitude": 3.012195445383676,
            "longitude": 101.58184814178546,
            "level": 5,
            "desc": "Trespasser alert event from CCTV-001"
        }
    }
    try:
        print(f"\n🚀 [DroneService] Calling DJI API...")
        response = requests.post(DJI_API_URL, headers=headers, json=payload_data, timeout=10)
        print(f"⬅️ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                return {"status": "success", "msg": "Drone Dispatched! 🚁", "data": data}
            else:
                return {"status": "error", "msg": f"DJI Error: {data.get('message')}"}
        else:
            return {"status": "error", "msg": f"HTTP Error {response.status_code}"}
    except Exception as e:
        print(f"[DroneService] Exception: {traceback.format_exc()}")
        return {"status": "error", "msg": str(e)}
