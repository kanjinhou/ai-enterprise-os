from django.urls import path
from .views import DetectionEventListCreateView, DashboardStatsView

urlpatterns = [
    path('events/', DetectionEventListCreateView.as_view(), name='detection-list-create'),
    path('dashboard/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
