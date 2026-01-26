from django.shortcuts import redirect
from django.utils import timezone
from django.urls import resolve


class SubscriptionCheckMiddleware:
    """
    订阅过期自动拦截中间件
    
    检查当前登录用户的 Customer 订阅状态：
    - 如果 subscription.expiration_date < today 或 is_active = False
    - 强制重定向到 /service-suspended/ 页面
    
    白名单（无条件允许访问）：
    - /admin/ (管理员后台)
    - /login/ (登录页)
    - /logout/ (登出页，允许过期用户退出登录)
    - 任何包含 'logout' 的路径（如 /admin/logout/）
    - /service-suspended/ (服务暂停页本身，避免死循环)
    - 静态文件 (/static/, /media/)
    - 超级管理员不受限制
    """
    
    # 白名单路径前缀
    EXEMPT_PATHS = [
        '/admin/',
        '/login/',
        '/service-suspended/',
        '/logout/',  # 允许用户退出登录
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        print(f"\n{'='*60}")
        print(f"DEBUG: SubscriptionCheckMiddleware - Request Path: {request.path}")
        print(f"DEBUG: User is {request.user}")
        print(f"DEBUG: Is Authenticated? {request.user.is_authenticated}")
        print(f"DEBUG: Is Superuser? {request.user.is_superuser}")
        
        # 检查是否在白名单中
        is_exempt = self._is_exempt_path(request.path)
        print(f"DEBUG: Is Exempt Path? {is_exempt}")
        if is_exempt:
            print(f"DEBUG: Path is exempt, skipping subscription check")
            return self.get_response(request)
        
        # 检查用户是否已登录
        if not request.user.is_authenticated:
            print(f"DEBUG: User not authenticated, skipping subscription check")
            return self.get_response(request)
        
        # 超级管理员不受限制
        if request.user.is_superuser:
            print(f"DEBUG: User is superuser, skipping subscription check")
            return self.get_response(request)
        
        # 检查订阅状态
        print(f"DEBUG: Checking subscription status...")
        is_expired = self._is_subscription_expired(request.user)
        print(f"DEBUG: Subscription Expired? {is_expired}")
        
        if is_expired:
            # 如果已经在服务暂停页面，避免重定向循环
            if request.path != '/service-suspended/':
                print(f"DEBUG: Redirecting to /service-suspended/")
                return redirect('/service-suspended/')
            else:
                print(f"DEBUG: Already on /service-suspended/, allowing access")
        
        print(f"{'='*60}\n")
        return self.get_response(request)
    
    def _is_exempt_path(self, path):
        """
        检查路径是否在白名单中
        
        豁免规则：
        1. 检查路径前缀是否在白名单中
        2. 检查是否包含 'logout' 关键词（允许用户退出登录）
        3. 检查静态文件和媒体文件
        """
        # 检查路径前缀白名单
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        
        # 检查是否包含 'logout' 关键词（允许任何形式的登出路径）
        # 例如：/logout/, /admin/logout/, /api/logout/ 等
        if 'logout' in path.lower():
            return True
        
        return False
    
    def _is_subscription_expired(self, user):
        """
        检查用户的订阅是否过期
        
        判断条件：
        1. Customer.is_active = False
        2. 或者 Subscription.expiration_date < today
        3. 或者 Subscription.is_active = False
        """
        try:
            from .models import UserProfile, Customer, Subscription
            
            print(f"  DEBUG: _is_subscription_expired - Starting check for user: {user.username}")
            
            # 获取用户档案
            try:
                user_profile = user.userprofile
                print(f"  DEBUG: UserProfile found: {user_profile}")
            except UserProfile.DoesNotExist:
                print(f"  DEBUG: UserProfile.DoesNotExist - User has no profile")
                return False
            
            customer = user_profile.customer
            print(f"  DEBUG: Customer: {customer.name} (ID: {customer.id})")
            print(f"  DEBUG: Customer.is_active: {customer.is_active}")
            
            # 检查 Customer 是否激活
            if not customer.is_active:
                print(f"  DEBUG: Customer is not active, subscription EXPIRED")
                return True
            
            # 检查是否有任何有效的订阅
            today = timezone.now().date()
            print(f"  DEBUG: Today's date: {today}")
            
            # 获取该客户的所有订阅
            subscriptions = Subscription.objects.filter(customer=customer)
            subscription_count = subscriptions.count()
            print(f"  DEBUG: Total subscriptions found: {subscription_count}")
            
            # 如果没有订阅，视为过期
            if not subscriptions.exists():
                print(f"  DEBUG: No subscriptions found, subscription EXPIRED")
                return True
            
            # 打印所有订阅的详细信息
            print(f"  DEBUG: Listing all subscriptions:")
            for idx, sub in enumerate(subscriptions, 1):
                expiration_date = sub.expiration_date.date()
                print(f"    [{idx}] Module: {sub.module.name}, is_active: {sub.is_active}, expiration_date: {expiration_date}")
            
            # 检查是否有至少一个有效订阅（激活且未过期）
            # 注意：expiration_date 是 DateTimeField，需要转换为日期进行比较
            valid_subscriptions = subscriptions.filter(
                is_active=True
            )
            valid_count = valid_subscriptions.count()
            print(f"  DEBUG: Active subscriptions count: {valid_count}")
            
            # 检查是否有未过期的订阅
            has_valid_subscription = False
            for subscription in valid_subscriptions:
                # 将 DateTimeField 转换为日期进行比较
                expiration_date = subscription.expiration_date.date()
                is_not_expired = expiration_date >= today
                print(f"  DEBUG: Subscription '{subscription.module.name}': expiration_date={expiration_date}, today={today}, is_not_expired={is_not_expired}")
                if is_not_expired:
                    has_valid_subscription = True
                    print(f"  DEBUG: Found valid subscription: {subscription.module.name}")
                    break
            
            # 如果没有有效订阅，返回 True（已过期）
            result = not has_valid_subscription
            print(f"  DEBUG: Final result - Subscription Expired: {result}")
            return result
            
        except Exception as e:
            # 如果出现任何错误（如用户没有 UserProfile），默认允许访问
            # 在生产环境中，你可能想要记录这个错误
            print(f"  DEBUG: Exception occurred: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"  DEBUG: Traceback:\n{traceback.format_exc()}")
            return False
