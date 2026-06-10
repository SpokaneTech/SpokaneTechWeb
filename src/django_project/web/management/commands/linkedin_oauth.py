from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from web.utilities.notifiers.linkedin import LinkedInOrganizationClient


class Command(BaseCommand):
    help = "Generate a LinkedIn OAuth authorization URL or exchange an authorization code for tokens."

    default_scope = "w_organization_social"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--code", help="Authorization code returned by LinkedIn.")
        parser.add_argument(
            "--redirect-uri",
            required=True,
            help="Redirect URI registered in the LinkedIn developer app.",
        )
        parser.add_argument(
            "--scope",
            default=self.default_scope,
            help=f"OAuth scopes to request. Defaults to: {self.default_scope}",
        )
        parser.add_argument("--state", help="Optional OAuth state value for the authorization URL.")
        parser.add_argument(
            "--show-url",
            action="store_true",
            help="Print the authorization URL even when --code is also provided.",
        )

    def handle(self, *args, **options) -> str:
        client_id = settings.LINKEDIN_CLIENT_ID
        client_secret = settings.LINKEDIN_CLIENT_SECRET
        env_path = getattr(settings, "ENV_PATH", None)

        if not client_id or not client_secret:
            raise CommandError("LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET must be configured.")

        client = LinkedInOrganizationClient(
            access_token=settings.LINKEDIN_ACCESS_TOKEN,
            organization_urn=settings.LINKEDIN_ORGANIZATION_URN or "",
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=settings.LINKEDIN_REFRESH_TOKEN,
            env_path=env_path,
        )

        redirect_uri = options["redirect_uri"]
        scope = options["scope"]
        state = options.get("state")
        code = options.get("code")
        show_url = options.get("show_url", False)

        if show_url or not code:
            auth_url = client.build_authorization_url(redirect_uri=redirect_uri, scope=scope, state=state)
            self.stdout.write("Open this URL in a browser and complete the LinkedIn consent flow:")
            self.stdout.write(auth_url)
            if not code:
                self.stdout.write("Re-run this command with --code once LinkedIn redirects back with ?code=...")
                return auth_url

        token_data = client.exchange_authorization_code(code=code, redirect_uri=redirect_uri)
        self.stdout.write(self.style.SUCCESS("LinkedIn tokens stored successfully."))
        self.stdout.write(f"Access token expires in: {token_data.get('expires_in')}")
        if token_data.get("refresh_token_expires_in") is not None:
            self.stdout.write(f"Refresh token expires in: {token_data.get('refresh_token_expires_in')}")
        elif not token_data.get("refresh_token"):
            self.stdout.write(
                self.style.WARNING(
                    "LinkedIn did not return a refresh token. Programmatic refresh may not be enabled for this app."
                )
            )
        return "LinkedIn OAuth token exchange completed."
