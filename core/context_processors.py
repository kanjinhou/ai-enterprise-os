from django.utils import timezone


def subscribed_modules(request):
    """
    上下文处理器：获取当前用户订阅的模块列表
    返回 {'subscribed_modules': ['ppe', 'drones', ...]}
    """
    # 如果用户未登录，返回空字典
    if not request.user.is_authenticated:
        return {'subscribed_modules': []}
    
    try:
        # 获取当前用户的 UserProfile 和 Customer
        from .models import UserProfile, Subscription
        
        user_profile = request.user.userprofile
        customer = user_profile.customer
        
        # 查询该 Customer 拥有的所有活跃且未过期的 Subscription
        active_subscriptions = Subscription.objects.filter(
            customer=customer,
            is_active=True,
            expiration_date__gt=timezone.now()
        ).select_related('module')
        
        # 提取 Module 的 slug 列表
        subscribed_slugs = [sub.module.slug for sub in active_subscriptions]
        
        return {'subscribed_modules': subscribed_slugs}
    
    except UserProfile.DoesNotExist:
        # 如果用户没有 UserProfile（例如 Admin 账号），返回空列表
        return {'subscribed_modules': []}
    except Exception:
        # 其他异常也返回空列表，防止页面报错
        return {'subscribed_modules': []}

