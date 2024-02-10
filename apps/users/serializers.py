from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

from apps.courses.models import Department, Institution
from apps.users.models import User


class CustomRegisterSerializer(RegisterSerializer):
    username = None
    email = serializers.EmailField(required=True)
    institution = serializers.PrimaryKeyRelatedField(queryset=Institution.objects.all())
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    name = serializers.CharField(required=True)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def get_cleaned_data(self):
        return {
            "email": self.validated_data.get("email", ""),
            "institution": self.validated_data.get("institution", None),
            "department": self.validated_data.get("department", None),
            "name": self.validated_data.get("name", ""),
            "password1": self.validated_data.get("password1", ""),
            "password2": self.validated_data.get("password2", ""),
        }


class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "name",
            "institution",
            "department",
        )


class FullUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "is_active",
            "is_staff",
            "institution",
            "department",
            "name",
        )
