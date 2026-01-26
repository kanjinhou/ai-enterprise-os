from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('violations/', views.violations, name='violations'),
    path('profile/', views.MyProfileView.as_view(), name='my-profile'),
    path('report/generate/', views.generate_report_view, name='report-generate'),
    path('drone/dispatch/', views.dispatch_drone_view, name='drone-dispatch'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('service-suspended/', views.service_suspended, name='service-suspended'),  # 服务暂停页面（已在中间件白名单中豁免）
]
