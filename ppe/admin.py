from django.contrib import admin
from .models import DetectionEvent


@admin.register(DetectionEvent)
class DetectionEventAdmin(admin.ModelAdmin):
    # 后台列表显示哪些字段
    list_display = ('customer', 'camera_id', 'timestamp', 'is_resolved')
    # 允许按客户和处理状态筛选
    list_filter = ('customer', 'is_resolved')
    # 允许搜索摄像头编号
    search_fields = ('camera_id',)
    # 按时间倒序排列
    ordering = ('-timestamp',)
