from django.db import models
from core.models import Customer


class DetectionEvent(models.Model):
    """PPE 检测事件模型 - 记录 AI 识别到的违规事件"""
    
    # 关联客户 (数据隔离：每个客户只能看到自己的记录)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='detection_events'
    )
    
    # 摄像头编号 (例如 "CAM-01")
    camera_id = models.CharField(max_length=50)
    
    # 违规抓拍照片
    image = models.ImageField(upload_to='detections/%Y/%m/%d/')
    
    # AI 识别结果 (JSON 格式存储检测框等信息)
    # 例如: {'helmet': false, 'bbox': [10, 10, 100, 100]}
    detections = models.JSONField(default=dict)
    
    # 事件发生时间
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # 是否已人工处理
    is_resolved = models.BooleanField(default=False)
    
    # 身份识别字段
    person_name = models.CharField(max_length=100, default="Unknown", blank=True)
    person_id = models.CharField(max_length=50, default="N/A", blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Detection Event'
        verbose_name_plural = 'Detection Events'

    def __str__(self):
        return f"{self.camera_id} - {self.person_name} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
