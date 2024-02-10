from django.urls import path

from apps.users.views import (
    CheckRegisteredView,
    GoogleLoginCallbackViewMobile,
    GoogleLoginView,
    GoogleLoginCallbackView,
)


urlpatterns = [
    path("google/login", GoogleLoginView.as_view(), name="google_login"),
    path(
        "google/login/callback",
        GoogleLoginCallbackView.as_view(),
        name="google_login_callback",
    ),
    path(
        "google/login/callback/mobile",
        GoogleLoginCallbackViewMobile.as_view(),
        name="google_login_callback_mobile",
    ),
    path("registered", CheckRegisteredView.as_view(), name="check_registered"),
]
