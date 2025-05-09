from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

# class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
#     def populate_user(self, request, sociallogin, data):
#         user = super().populate_user(request, sociallogin, data)
#         user.first_name = data.get("first_name") or data.get("given_name", "")
#         user.last_name = data.get("last_name") or data.get("family_name", "")
#         return user


# class NoSignupConfirmationAdapter(DefaultSocialAccountAdapter):
#     def is_auto_signup_allowed(self, request, sociallogin):
#         """
#         Always return True to bypass signup confirmation page.
#         """
#         return True

#     def populate_user(self, request, sociallogin, data):
#         """
#         Optional: auto-fill first_name/last_name from Google data.
#         """
#         user = super().populate_user(request, sociallogin, data)
#         user.first_name = data.get("first_name", "")
#         user.last_name = data.get("last_name", "")
#         return user


class NoSignupSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        return True  # Always allow auto signup
