from authlib.integrations.starlette_client import OAuth

from settings import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET


class OAuthConfig:
    def __init__(self):
        self.oauth = OAuth()
        self.base_url_github = "https://github.com"
        self.api_base_url_github = "https://api.github.com"

        self._register_providers()

    def _register_providers(self):
        if GITHUB_CLIENT_SECRET and GITHUB_CLIENT_ID:
            self.oauth.register(
                name="github",
                client_id=GITHUB_CLIENT_ID,
                client_secret=GITHUB_CLIENT_SECRET,
                client_kwargs={"scope": "user:email"},
                authorize_url=f"{self.base_url_github}/login/oauth/authorize",
                access_token_url=f"{self.base_url_github}/login/oauth/access_token",
                userinfo_endpoint=f"{self.api_base_url_github}/user",
                api_base_url=self.api_base_url_github,
            )

    def get_client(self, provider: str):
        return getattr(self.oauth, provider, None)


oauth_config = OAuthConfig()
