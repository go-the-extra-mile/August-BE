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
    def save_user(self, request, sociallogin, form=None):
        from allauth.socialaccount.adapter import get_account_adapter

        u = sociallogin.user
        u.set_unusable_password()
        if form:
            get_account_adapter().save_user(request, u, form)
        else:
            get_account_adapter().populate_username(request, u)

        # Set institution, department, and name
        oauth_data = sociallogin.account.extra_data
        u.institution_id = 1
        u.department_id = 1
        u.name = oauth_data.get("name")

        sociallogin.save(request)
        return u
