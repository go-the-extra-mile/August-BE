from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from config.settings.base import get_secret

class GoogleOAuthCallbackView(APIView):
    def get(self, request):
        # code 값을 URL의 query string에서 추출
        code = request.query_params.get("code")
        if code:
            response = self.forward_code_to_google_login_view(code)
            if response.status_code == 200:
                return Response(response.json(), status=status.HTTP_200_OK)

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

        return Response(
            {"error": "Code not provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    def forward_code_to_google_login_view(self, code: str):
        url = "http://127.0.0.1:8000/dj-rest-auth/google/"
        payload = {"code": code}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        return response


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://127.0.0.1:8000/dj-rest-auth/google/login/callback"
    client_class = OAuth2Client
