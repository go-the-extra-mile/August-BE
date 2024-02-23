from django.urls import path

from apps.users.views import (
    CheckRegisteredView,
    GoogleLoginView,
    GoogleLoginCallbackView,
    UserView,
)


urlpatterns = [
    path("google/login", GoogleLoginView.as_view(), name="google_login"),
    path(
        "google/login/callback",
        GoogleLoginCallbackView.as_view(),
        name="google_login_callback",
    ),
    path("registered", CheckRegisteredView.as_view(), name="check_registered"),
    path("<int:pk>", UserView.as_view(), name='user_detail'),
]
