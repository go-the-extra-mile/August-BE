from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        # Call the original save_user method
        user = super().save_user(request, user, form, commit=False)
        # Get the department from the form data
        department = form.cleaned_data.get("department")
        # Assign the department to the user instance
        user.department = department
        # Get the institution from the form data
        institution = form.cleaned_data.get("institution")
        # Assign the institution to the user instance
        user.institution = institution
        # Save the user instance
        user.save()
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        oauth_data = sociallogin.account.extra_data
        user.name = oauth_data.get("name")
        user.profile_image_url = oauth_data.get("picture")

        return user
