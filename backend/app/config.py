"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"
    # Comma-separated list of allowed frontend origins for CORS. Supports the
    # site's multiple domains (e.g. the custom domain + the default Vercel URL).
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def frontend_origins(self) -> list[str]:
        """Parse frontend_url into a list of origins for CORS allow_origins."""
        return [o.strip() for o in self.frontend_url.split(",") if o.strip()]


settings = Settings()
