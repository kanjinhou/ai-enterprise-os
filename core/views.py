from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import UserProfile, Subscription
from .serializers import UserProfileSerializer
from .utils.report_generator import generate_daily_report
from .utils import drone_service


def check_module_permission(user, module_slug):
    """检查用户是否拥有指定模块的订阅权限"""
    try:
        customer = user.userprofile.customer
        return Subscription.objects.filter(
            customer=customer,
            module__slug=module_slug,
            is_active=True,
            expiration_date__gt=timezone.now()
        ).exists()
    except (UserProfile.DoesNotExist, AttributeError):
        return False


@login_required
def index(request):
    """首页 - 仪表盘"""
    # 检查高级模块权限
    has_llm_permission = check_module_permission(request.user, 'ppe_llm')
    has_drone_permission = check_module_permission(request.user, 'ppe_drone')
    
    context = {
        'has_llm_permission': has_llm_permission,
        'has_drone_permission': has_drone_permission,
    }
    return render(request, 'dashboard.html', context)


@login_required
def violations(request):
    """违规列表页面"""
    return render(request, 'violations.html')


@login_required
def generate_report_view(request):
    """
    LLM 智能报告生成接口。
    要求用户拥有 ppe_llm 模块权限，返回当日 Markdown 报告。
    """
    if not check_module_permission(request.user, 'ppe_llm'):
        return JsonResponse(
            {'error': '此功能需要订阅 [AI Reporting] 模块，请联系销售。'},
            status=403
        )
    try:
        customer = request.user.userprofile.customer
    except (UserProfile.DoesNotExist, AttributeError):
        return JsonResponse(
            {'error': '用户档案或客户信息不存在。'},
            status=403
        )
    report_text = generate_daily_report(customer)
    return JsonResponse({'report': report_text})


@login_required
def dispatch_drone_view(request):
    """
    无人机调度接口。
    要求用户拥有 ppe_drone 模块权限，或为 superuser。
    """
    # 权限检查：ppe_drone 权限或 superuser
    has_permission = (
        request.user.is_superuser or 
        check_module_permission(request.user, 'ppe_drone')
    )
    
    if not has_permission:
        return JsonResponse(
            {'error': '此功能需要订阅 [Drone Support] 模块，请联系销售。'},
            status=403
        )
    
    # 调用无人机服务
    result = drone_service.trigger_mission()
    
    if result['status'] == 'success':
        return JsonResponse(result)
    else:
        return JsonResponse(result, status=500)


def service_suspended(request):
    """服务已暂停页面"""
    return render(request, 'core/suspended.html')


class MyProfileView(APIView):
    """获取当前登录用户的档案信息"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_profile = request.user.userprofile
            serializer = UserProfileSerializer(user_profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': '用户档案不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
