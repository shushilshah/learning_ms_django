from django.urls import path
from . import views

urlpatterns = [
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name="teacher_dashboard"),
    path('teacher/course/create/', views.create_course, name="create_course"),
    path('teacher/course/<int:course_id>/module/create/',
         views.create_module, name="create_module"),
    path('teacher/course/<int:course_id>/',
         views.teacher_course_detail, name="teacher_course_detail"),
    path('teacher/module/<int:module_id>/lesson/create/',
         views.create_lesson, name='create_lesson'),
    path('student/dashboard/', views.student_dashboard, name="student_dashboard"),
    path('role/', views.role_redirect, name="role_redirect"),
    path("", views.learning_dashboard, name="learning_dashboard"),

    path('course/', views.course_list, name='course_list'),
    path('course/<int:course_id>/',
         views.course_detail, name='course_detail'),
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('module/<int:module_id>/', views.module_detail, name='module_detail'),
    # path("accounts/login/",
    #      auth_views.LoginView.as_view(template_name='login.html'), name='login')

    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/attempt/<int:attempt_id>/submit/',
         views.submit_quiz, name='submit_quiz'),
    path('quiz/attempt/<int:attempt_id>/result/',
         views.quiz_result, name='quiz_result'),
]
