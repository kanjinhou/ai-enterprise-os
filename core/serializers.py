from rest_framework import serializers
from .models import Customer, UserProfile


class CustomerSerializer(serializers.ModelSerializer):
    """序列化 Customer 模型"""
    class Meta:
        model = Customer
        fields = '__all__'


class UserProfileSerializer(serializers.ModelSerializer):
    """序列化 UserProfile 模型，嵌套包含 customer 信息"""
    customer = CustomerSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'
