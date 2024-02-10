from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from config.settings.base import get_secret


class GoogleLoginView(APIView):
    def get(self, request, *args, **kwargs):
        client_id = get_secret("GOOGLE_WEB_CLIENT_ID")
        redirect_uri = get_secret("DEPLOY_HOST_PORT") + "/users/google/login/callback"
        response_type = "code"
        scope = "profile%20email"
        url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&scope={scope}"
        print(url)
        return redirect(url)


class GoogleLoginCallbackView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = get_secret("DEPLOY_HOST_PORT") + "/users/google/login/callback"
    client_class = OAuth2Client

    def get(self, request, *args, **kwargs):
        code = request.query_params.get("code", None)
        error = request.query_params.get("error", None)
        if error:
            return Response(data={"error": error}, status=status.HTTP_400_BAD_REQUEST)

        self.request.data.update({"code": code})
        print(f"code: {code}")

        return self.post(request, args, kwargs)
    
class GoogleLoginCallbackViewMobile(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = ""
    client_class = OAuth2Client