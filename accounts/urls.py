from django.urls import path
from .views import SignupAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('signup/', SignupAPIView.as_view(), name='api_signup'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('profile/', ProfileAPIView.as_view(), name='api_profile'),
    # path('users/', UserListAPIView.as_view(), name='api_users'),
]
