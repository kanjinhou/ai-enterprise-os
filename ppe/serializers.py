from rest_framework import serializers
from .models import DetectionEvent


class DetectionEventSerializer(serializers.ModelSerializer):
    """检测事件序列化器"""
    
    class Meta:
        model = DetectionEvent
        fields = '__all__'
        # customer 字段只读，由后台自动设置，防止前端篡改
        read_only_fields = ('customer',)
