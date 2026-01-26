"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from core.views import index, service_suspended

urlpatterns = [
    path("", index, name='index'),  # 首页
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path("logout/", auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path("service-suspended/", service_suspended, name='service-suspended'),  # 服务暂停页面（独立路由，不在 API 路径下）
    path("api/v1/", include("core.urls")),
    path("api/v1/ppe/", include("ppe.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
