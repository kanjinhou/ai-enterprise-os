import cv2
import math
import time
import requests
import os
import numpy as np
import face_recognition
from ultralytics import YOLO

# --- 配置部分 ---
SERVER_URL = "http://127.0.0.1:8000/api/v1/ppe/events/"
CAMERA_ID = "CAM-01"
CONFIDENCE_THRESHOLD = 0.5
FACE_DB_DIR = "authorized_faces"

# API 认证信息
USERNAME = "admin"
PASSWORD = "admin123"

# --- 1. 加载人脸数据库 (带内存修复) ---
print(f"🔄 Loading Employee Database from '{FACE_DB_DIR}'...")
known_face_encodings = []
known_face_names = []
known_face_ids = []

if not os.path.exists(FACE_DB_DIR):
    os.makedirs(FACE_DB_DIR)
    print(f"⚠️ Warning: Directory '{FACE_DB_DIR}' created. Please put photos there!")
else:
    for filename in os.listdir(FACE_DB_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                # 解析文件名
                name_part = os.path.splitext(filename)[0]
                if "_" in name_part:
                    emp_id, emp_name = name_part.split("_", 1)
                else:
                    emp_id, emp_name = "N/A", name_part
                
                image_path = os.path.join(FACE_DB_DIR, filename)
                
                # [关键修复 1] 加载图片后，强制转为连续内存
                image = face_recognition.load_image_file(image_path)
                image = np.ascontiguousarray(image) 
                
                # 获取特征
                encodings = face_recognition.face_encodings(image)
                
                if len(encodings) > 0:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(emp_name)
                    known_face_ids.append(emp_id)
                    print(f"  ✅ Loaded Identity: {emp_name} (ID: {emp_id})")
                else:
                    print(f"  ⚠️ No face found in {filename}")
                    
            except Exception as e:
                print(f"  ❌ Error loading {filename}: {e}")

print(f"✅ Database Ready. Total profiles: {len(known_face_names)}")

# --- 2. 加载 YOLO 模型 ---
print("🔄 Loading YOLOv8 Model...")
model = YOLO("yolov8n.pt") 
classNames = model.names 

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

print("🚀 Surveillance System Started!")

while True:
    success, img = cap.read()
    if not success or img is None:
        continue 

    # === A. 人脸识别处理 (Face Recognition) ===
    # 缩小图片
    img_small = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
    
    # [关键修复 2] BGR 转 RGB 后，再次强制转为连续内存，防止 dlib 崩溃
    rgb_small_frame = img_small[:, :, ::-1]
    rgb_small_frame = np.ascontiguousarray(rgb_small_frame)

    # 查找人脸
    try:
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        current_persons = [] 

        for face_encoding, face_loc in zip(face_encodings, face_locations):
            name = "Unknown"
            emp_id = "N/A"
            
            # 只有当数据库不为空时才进行比对
            if len(known_face_encodings) > 0:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]
                        emp_id = known_face_ids[best_match_index]
            
            current_persons.append({'name': name, 'id': emp_id})

            # 画框 (转换坐标回原图)
            top, right, bottom, left = face_loc
            top *= 4; right *= 4; bottom *= 4; left *= 4 
            cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(img, f"{name}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
    except Exception as e:
        # 如果人脸识别偶尔出错，打印但不崩溃
        print(f"Face Rec Error: {e}")
        current_persons = []

    # === B. YOLO 物体检测 ===
    results = model(img, stream=True, verbose=False)
    violation_detected = False
    violation_type = ""

    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            conf = math.ceil((box.conf[0] * 100)) / 100
            cls = int(box.cls[0])
            label = classNames[cls]

            if conf > CONFIDENCE_THRESHOLD:
                color = (255, 0, 0)
                # 演示逻辑: 检测到人且按S键时
                if label == "person": 
                    violation_detected = True
                    violation_type = "No Safety Gear"
                    color = (0, 0, 255)

                cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                cv2.putText(img, f'{label} {conf}', (max(0, x1), max(35, y1)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    # === C. 显示与上传 ===
    who_is_it = "Unknown"
    who_id = "N/A"
    if 'current_persons' in locals() and len(current_persons) > 0:
        who_is_it = current_persons[0]['name']
        who_id = current_persons[0]['id']

    status_text = f"ID: {who_is_it} | Check: {violation_detected}"
    cv2.putText(img, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("AI Enterprise OS - Camera 01", img)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    
    # 按 's' 键手动触发报警
    if key == ord('s') and violation_detected:
        print(f"🚀 Reporting Violation for: {who_is_it}...")
        try:
            _, img_encoded = cv2.imencode('.jpg', img)
            files = {'image': ('capture.jpg', img_encoded.tobytes(), 'image/jpeg')}
            data = {
                'camera_id': CAMERA_ID,
                'detections': '{"items": [{"class": "' + violation_type + '", "confidence": 0.95}]}',
                'person_name': who_is_it,
                'person_id': who_id
            }
            # 发送请求（带认证）
            response = requests.post(SERVER_URL, data=data, files=files, auth=(USERNAME, PASSWORD))
            if response.status_code in [200, 201]:
                print("✅ Alert Sent to Django!")
            else:
                print(f"❌ Upload Failed: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"❌ Upload Failed: {e}")

cap.release()
cv2.destroyAllWindows()
