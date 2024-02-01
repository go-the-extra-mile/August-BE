from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class GoogleOAuthCallbackView(APIView):
    def get(self, request):
        # code 값을 URL의 query string에서 추출
        code = request.query_params.get("code")
        if code:
            response = self.forward_code_to_google_login_view(code)
            if response.status_code == 200:
                return Response(response.json(), status=status.HTTP_200_OK)

            print(response)
            return Response(
                {"error": "Failed to process with GoogleLoginView"},
                status=response.status_code,
            )

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
