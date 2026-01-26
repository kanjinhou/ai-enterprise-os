from django.shortcuts import render
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import DetectionEvent
from .serializers import DetectionEventSerializer
from core.utils.notification_service import NotificationService


class DetectionEventListCreateView(generics.ListCreateAPIView):
    """
    检测事件列表和创建视图
    - GET: 获取当前用户所属公司的所有检测事件
    - POST: 创建新的检测事件（自动关联到当前用户的公司）
    """
    serializer_class = DetectionEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """只返回当前用户所属 Customer 的数据"""
        return DetectionEvent.objects.filter(
            customer=self.request.user.userprofile.customer
        )

    def perform_create(self, serializer):
        """保存时自动设置 customer 为当前用户所属的公司，并触发报警"""
        # 从请求数据中提取身份信息（如果前端没传，使用默认值）
        person_name = self.request.data.get('person_name', 'Unknown')
        person_id = self.request.data.get('person_id', 'N/A')
        
        # 保存事件，包含身份信息
        event = serializer.save(
            customer=self.request.user.userprofile.customer,
            person_name=person_name,
            person_id=person_id
        )
        
        # 触发 WhatsApp 报警（异步发送，不阻塞 API 响应）
        try:
            NotificationService.send_whatsapp_alert(event)
        except Exception as e:
            # 报警失败不应影响事件保存，仅记录错误
            print(f"[Notification Error] Failed to send alert for event {event.id}: {e}")


class DashboardStatsView(APIView):
    """
    Dashboard 统计数据接口
    返回用于渲染图表的统计数据
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 获取当前用户所属公司的所有检测事件
        customer = request.user.userprofile.customer
        events = DetectionEvent.objects.filter(customer=customer)

        # 1. 总违规数
        total_events = events.count()

        # 2. 未处理的违规数
        unresolved_count = events.filter(is_resolved=False).count()

        # 3. 按摄像头分组统计 (用于饼图)
        camera_stats = list(
            events.values('camera_id')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # 4. 过去 7 天每天的违规数量 (用于折线图)
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)
        
        # 按日期分组统计
        daily_stats = dict(
            events.filter(timestamp__date__gte=seven_days_ago)
            .values('timestamp__date')
            .annotate(count=Count('id'))
            .values_list('timestamp__date', 'count')
        )
        
        # 补全过去 7 天的数据（没有记录的日期填 0）
        recent_trend = []
        for i in range(7):
            date = seven_days_ago + timedelta(days=i)
            recent_trend.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': daily_stats.get(date, 0)
            })

        return Response({
            'total_events': total_events,
            'unresolved_count': unresolved_count,
            'camera_stats': camera_stats,
            'recent_trend': recent_trend,
        })
