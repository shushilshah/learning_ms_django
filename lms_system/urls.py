"""
URL configuration for lms_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from courses import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.learning_dashboard, name="learning_dashboard"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path('course/', views.course_list, name='course_list'),
    path('course/<int:course_id>/',
         views.course_detail, name='course_detail'),
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('module/<int:module_id>/', views.module_detail, name='module_detail'),
    # path("accounts/login/",
    #      auth_views.LoginView.as_view(template_name='login.html'), name='login')
    path('accounts/', include('django.contrib.auth.urls')),
    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/attempt/<int:attempt_id>/submit/',
         views.submit_quiz, name='submit_quiz'),
    path('quiz/attempt/<int:attempt_id>/result/',
         views.quiz_result, name='quiz_result'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
