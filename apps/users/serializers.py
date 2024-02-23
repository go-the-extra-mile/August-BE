from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
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


class ImageOrUrlField(serializers.ImageField):
    """
    User's profile image can be saved in `profile_image_file` field or exist as a URL in `profile_image_url`.
    User's profile image is always serialized as a URL.
    """

    def to_representation(self, value):
        # Case 1: URL Field
        if isinstance(value, str):
            return value
        # Case 2: Image Field
        return super().to_representation(value)

    def to_internal_value(self, data):
        return super().to_internal_value(data)


class CustomUserDetailsSerializer(UserDetailsSerializer):
    profile_image = ImageOrUrlField()
    institution_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Institution.objects.all(), source="institution"
    )
    department_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Department.objects.all(), source="department"
    )

    class Meta(UserDetailsSerializer.Meta):
        extra_fields = [
            "email",
            "name",
            "institution",
            "institution_id",
            "department",
            "department_id",
            "profile_image",
            "year_in_school",
        ]
        fields = ("id", *extra_fields)
        read_only_fields = ("email", "institution", "department")
        depth = 1


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
            "profile_image",
            "year_in_school",
        )
        read_only_fields = ("email",)
