from django.contrib import admin
from .models import Customer, UserProfile, Module, Subscription

# 注册 Customer 表到后台
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # 后台列表显示哪些字段
    list_display = ('name', 'license_key', 'is_active', 'created_at')
    # 允许搜索公司名
    search_fields = ('name',)
    # 允许按激活状态过滤
    list_filter = ('is_active',)


# 注册 UserProfile 表到后台
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # 后台列表显示哪些字段
    list_display = ('user', 'customer', 'role')
    # 允许搜索用户名和客户名
    search_fields = ('user__username', 'customer__name')
    # 允许按角色过滤
    list_filter = ('role',)


# 注册 Module 表到后台
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    # 后台列表显示哪些字段
    list_display = ('name', 'slug', 'price')
    # 允许搜索模块名
    search_fields = ('name', 'slug')
    # 自动生成 slug
    prepopulated_fields = {'slug': ('name',)}


# 注册 Subscription 表到后台
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    # 后台列表显示哪些字段
    list_display = ('customer', 'module', 'is_active', 'expiration_date', 'is_valid_display')
    # 允许搜索客户名和模块名
    search_fields = ('customer__name', 'module__name')
    # 允许按激活状态和模块过滤
    list_filter = ('is_active', 'module')
    # 按过期时间排序
    ordering = ('-expiration_date',)
    
    def is_valid_display(self, obj):
        """显示订阅是否有效"""
        return obj.is_valid
    is_valid_display.boolean = True
    is_valid_display.short_description = 'Valid'