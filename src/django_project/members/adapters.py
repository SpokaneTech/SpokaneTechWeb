from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if request.user.is_authenticated:
            return

        email = sociallogin.user.email
        if not email:
            return

        User = get_user_model()

        try:
            existing_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return

        linked_accounts = SocialAccount.objects.filter(user=existing_user)
        existing_providers = {acct.provider for acct in linked_accounts}
        current_provider = sociallogin.account.provider

        if current_provider not in existing_providers:
            # Set a toastable message
            if existing_providers:
                msg: str = (
                    f"This account is already registered using: <b>{', '.join(existing_providers)}</b>. Please login using that provider."
                )
            else:
                msg = "This account is already registered. Please login using the appropriate provider."
            messages.error(request, msg)
            raise ImmediateHttpResponse(redirect("/members/login/"))

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # Provide safe defaults to required custom user model fields
        user.first_name = user.first_name or ""
        user.last_name = user.last_name or ""
        user.title = user.title or ""
        user.zip_code = user.zip_code or ""
        user.city = user.city or ""
        user.state = user.state or ""

        return user
