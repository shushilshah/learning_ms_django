from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('signup/', SignupAPIView.as_view(), name='api_signup'),
    path("login/", LoginAPIView.as_view(), name="api_login"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('courses/', CourseListAPIView.as_view(), name="api_course_list"),
    path("courses/<int:course_id>/enroll/", EnrollCourseAPIView.as_view(), name="api_enroll_course"),
    path("lessons/<int:lesson_id>/", LessonDetailAPIView.as_view(), name="api_lesson"),
    path("modules/<int:module_id>/", ModuleDetailAPIView.as_view(), name="api_module"),
    path('lessons/<int:lesson_id>/progress/', LessonProgressAPIView.as_view(), name='api_lesson_progress'),
    path('dashboard/', LearningDashboardAPIView.as_view(), name='api_learning_dashboard'),
    path('teacher/dashboard/', TeacherDashboardAPIView.as_view(), name='api_teacher_dashboard'),
    path('teacher/courses/create/', CreateCourseTeacherAPIView.as_view(), name="api_create_course_teacher"),
    path('teacher/courses/<int:course_id>/edit/', EditCourseTeacherAPIView.as_view(), name="api_edit_course_teacher"),
    path('teacher/courses/<int:course_id>/modules/create/', CreateModuleTeacherAPIView.as_view(), name="api_create_module_teacher"),
    path('teacher/courses/detail/', TeacherCourseDetailAPIView.as_view(), name="api_course_detail_teacher"),
    path('teacher/lessons/create/', CreateLessonTeacherAPIView.as_view(), name="api_crate_lesson_teacher"),
    path('student/courses/<int:course_id>/resume/', ResumeCourseStudentAPIView.as_view(), name="api_resume_course_student"),
    path('student/lessons/<int:course_id>/complete/', MarkLessonCompleteAPIView.as_view(), name="api_mark_lesson_complete_student"),
    path('student/lessons/<int:lesson_id>/time-spent/', UpdateTimeSpentStudentAPIView.as_view(), name="api_update_time_spent")
    # path('profile/', ProfileAPIView.as_view(), name='api_profile'),
    # path('users/', UserListAPIView.as_view(), name='api_users'),
]
