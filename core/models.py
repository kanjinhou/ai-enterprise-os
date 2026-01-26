from django.db import models
from django.contrib.auth.models import User
import uuid

# 这就是我们的“租户”模型
class Customer(models.Model):
    # 公司名称 (比如: "Shell Petroleum", "Petronas")
    name = models.CharField(max_length=100)
    
    # 唯一的 License Key (类似于序列号，我们用 UUID 生成)
    license_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # 是否激活 (如果没交钱，把这个勾去掉，他们就登不进去了)
    is_active = models.BooleanField(default=True)
    
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({str(self.license_key)[:8]}...)"


# 用户档案模型 - 建立 User 和 Customer 的强关联
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]
    
    # 一对一关联 Django 内置的 User 模型
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # 外键关联 Customer (一个客户可以有多个用户)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='users')
    
    # 用户角色
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.customer.name}"


# 模块/插件模型 - 定义系统可用的功能模块
class Module(models.Model):
    # 模块名称 (例如 "PPE Detection")
    name = models.CharField(max_length=100)
    
    # 唯一标识符 (例如 "ppe")
    slug = models.SlugField(unique=True)
    
    # 模块描述
    description = models.TextField(blank=True)
    
    # 月费价格 (可选)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name


# 订阅/授权模型 - 管理客户对模块的订阅
class Subscription(models.Model):
    # 关联客户
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    
    # 关联模块
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    
    # 是否激活
    is_active = models.BooleanField(default=True)
    
    # 过期时间
    expiration_date = models.DateTimeField()
    
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 确保同一个 Customer 对同一个 Module 只能有一条记录
        unique_together = ['customer', 'module']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.customer.name} - {self.module.name}"
    
    @property
    def is_valid(self):
        """检查订阅是否有效（激活且未过期）"""
        from django.utils import timezone
        return self.is_active and self.expiration_date > timezone.now()