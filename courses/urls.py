from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_user, name="login_user"),
    path("signup/", views.signup_view, name='signup'),
    path("logout/", views.logout_user, name="logout_user"),
    path('profile/', views.profile_view, name='profile'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name="teacher_dashboard"),
    path('teacher/course/create/', views.create_course, name="create_course"),
    path('teacher/course/<int:course_id>/edit/',
         views.edit_course, name="edit_course"),
    path('teacher/course/<int:course_id>/module/create/',
         views.create_module, name="create_module"),
    path('teacher/course/<int:course_id>/',
         views.teacher_course_detail, name="teacher_course_detail"),
    path('teacher/module/<int:module_id>/lesson/create/',
         views.create_lesson, name='create_lesson'),
    path('student/dashboard/', views.student_dashboard, name="student_dashboard"),
    path('role/', views.role_redirect, name="role_redirect"),
    path("learning_dashboard/", views.learning_dashboard,
         name="learning_dashboard"),

    path('course/', views.course_list, name='course_list'),
    path("enroll/<int:course_id>/", views.enroll_course, name="enroll_course"),
    path('course/<int:course_id>/',
         views.course_detail, name='course_detail'),
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lessons/<int:lesson_id>/complete/',
         views.mark_lesson_complete, name="lesson_complete"),
    path('module/<int:module_id>/', views.module_detail, name='module_detail'),
    path("course/<int:course_id>/resume/", views.resume_course, name="resume_course"),
    # path("accounts/login/",
    #      auth_views.LoginView.as_view(template_name='login.html'), name='login')

    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/attempt/<int:attempt_id>/submit/',
         views.submit_quiz, name='submit_quiz'),
    path('quiz/attempt/<int:attempt_id>/result/',
         views.quiz_result, name='quiz_result'),
]
