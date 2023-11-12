from . import views
from authentication.api import views as api_view
from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)
from django.contrib.auth.decorators import login_required

app_name = "api"


urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("register/", api_view.RegisterView.as_view(), name="register"),
    path("login/", api_view.LoginAPIView.as_view(), name="login"),
    path("logout/", api_view.LogoutAPIView.as_view(), name="logout"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
