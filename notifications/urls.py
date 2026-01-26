from django.urls import path
from . import views

urlpatterns = [
    path('admin/publish/', views.admin_publish_notice, name="admin_publish_notice"),
    path('teacher/publish/', views.teacher_publish_notice, name="teacher_publish_notice"),
    path('list/', views.notifications_list, name="notifications_list"),
    path('mark-read/<int:pk>/', views.mark_notification_read, name="mark_notification_read"),
    path('teacher/list/', views.teacher_notice_list, name='teacher_notice_list'),
    path('student/list/', views.student_notifications, name="student_notifications"),
    path('notice-redirect/', views.notice_redirect, name="notice_redirect"),

]